"""
Domain-specific embedding model adaptation.

This module provides tools for fine-tuning and adapting embedding models
to specific domains and industries, improving semantic search, recommendations,
and context management for specialized applications.
"""

import asyncio
import json
import logging
import os
import pickle
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field, validator

try:
    import torch
    from torch.utils.data import Dataset, DataLoader

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from sentence_transformers import SentenceTransformer, InputExample, losses
    from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class FineTuningMethod(str, Enum):
    """Method to use for fine-tuning embedding models."""

    CONTRASTIVE = "contrastive"
    TRIPLET = "triplet"
    MULTIPLE_NEGATIVES = "multiple_negatives"
    SUPERVISED = "supervised"
    DOMAIN_ADAPTATION = "domain_adaptation"
    KNOWLEDGE_DISTILLATION = "knowledge_distillation"


class EmbeddingTrainingConfig(BaseModel):
    """Configuration for embedding model training."""

    batch_size: int = 16
    num_epochs: int = 3
    warmup_steps: int = 100
    learning_rate: float = 2e-5
    max_seq_length: int = 256
    evaluation_steps: int = 500
    save_best_model: bool = True
    early_stopping_patience: Optional[int] = 3
    use_amp: bool = True  # Automatic Mixed Precision
    train_test_split: float = 0.1
    random_seed: int = 42
    checkpoint_path: str | None = None
    checkpoint_save_steps: int = 1000


class EmbeddingAdapterConfig(BaseModel):
    """Configuration for domain embedding adaptation."""

    base_model: str = "all-MiniLM-L6-v2"
    domain: str
    method: FineTuningMethod = FineTuningMethod.CONTRASTIVE
    training: EmbeddingTrainingConfig = Field(default_factory=EmbeddingTrainingConfig)
    cache_dir: str | None = None
    output_dir: str
    description: str | None = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tokenizer_params: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("output_dir")
    def validate_output_dir(cls, v):
        """Validate that output directory exists or create it."""
        if not os.path.exists(v):
            os.makedirs(v)
        return v


class DomainDataset(Dataset):
    """Dataset for domain-specific embedding training."""

    def __init__(self, examples):
        self.examples = examples

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]


class DomainEmbeddingAdapter:
    """
    Domain-specific embedding model adapter.

    This class provides tools for fine-tuning embedding models for specific
    domains and industries, improving semantic search, recommendations,
    and context understanding for specialized applications.
    """

    def __init__(
        self, config: EmbeddingAdapterConfig, logger: logging.Logger | None = None
    ):
        """
        Initialize the domain embedding adapter.

        Args:
            config: Configuration for domain adaptation
            logger: Optional logger
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Check dependencies
        if not HAS_TORCH or not HAS_SENTENCE_TRANSFORMERS:
            self.logger.warning(
                "PyTorch and SentenceTransformers are required for domain adaptation. "
                "Please install with: pip install torch sentence-transformers"
            )

        # Initialize model as None
        self.model = None
        self.is_fine_tuned = False
        self.evaluation_results = {}

        # Initialize evaluation and dataset attributes
        self.train_dataset = None
        self.dev_dataset = None
        self.evaluator = None

    async def initialize(self) -> None:
        """Initialize the domain embedding adapter."""
        if not HAS_TORCH or not HAS_SENTENCE_TRANSFORMERS:
            self.logger.error("Required dependencies not installed")
            return

        try:
            # Load base model
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(
                    self.config.base_model, cache_folder=self.config.cache_dir
                ),
            )

            # Check if fine-tuned model exists
            fine_tuned_path = os.path.join(
                self.config.output_dir, f"{self.config.domain}_model"
            )
            if os.path.exists(fine_tuned_path):
                self.logger.info(f"Loading fine-tuned model from {fine_tuned_path}")
                self.model = await loop.run_in_executor(
                    None, lambda: SentenceTransformer(fine_tuned_path)
                )
                self.is_fine_tuned = True

                # Load evaluation results if available
                eval_path = os.path.join(
                    self.config.output_dir, f"{self.config.domain}_eval.json"
                )
                if os.path.exists(eval_path):
                    with open(eval_path, "r") as f:
                        self.evaluation_results = json.load(f)

        except Exception as e:
            self.logger.error(f"Error initializing domain embedding adapter: {e}")
            raise

    async def prepare_contrastive_data(
        self,
        positive_pairs: list[Tuple[str, str]],
        negative_pairs: Optional[list[Tuple[str, str]]] = None,
        hard_negatives: Optional[Dict[str, list[str]]] = None,
    ) -> None:
        """
        Prepare data for contrastive learning.

        Args:
            positive_pairs: List of (text1, text2) tuples that are similar
            negative_pairs: Optional list of (text1, text2) tuples that are dissimilar
            hard_negatives: Optional dict mapping text to list of hard negative examples
        """
        if not HAS_TORCH or not HAS_SENTENCE_TRANSFORMERS:
            self.logger.error("Required dependencies not installed")
            return

        train_examples = []

        # Process positive pairs
        for text1, text2 in positive_pairs:
            train_examples.append(InputExample(texts=[text1, text2], label=1.0))

        # Process negative pairs if provided
        if negative_pairs:
            for text1, text2 in negative_pairs:
                train_examples.append(InputExample(texts=[text1, text2], label=0.0))

        # Process hard negatives if provided
        if hard_negatives:
            for anchor, negatives in hard_negatives.items():
                for negative in negatives:
                    train_examples.append(
                        InputExample(texts=[anchor, negative], label=0.0)
                    )

        # Split into train and dev
        train_test_split = self.config.training.train_test_split
        if train_test_split > 0:
            train_size = int(len(train_examples) * (1 - train_test_split))

            # Shuffle examples
            import random

            random.seed(self.config.training.random_seed)
            random.shuffle(train_examples)

            self.train_dataset = DomainDataset(train_examples[:train_size])
            self.dev_dataset = DomainDataset(train_examples[train_size:])

            # Create evaluator from dev set
            self.evaluator = EmbeddingSimilarityEvaluator.from_input_examples(
                train_examples[train_size:], name=f"{self.config.domain}_dev"
            )
        else:
            self.train_dataset = DomainDataset(train_examples)
            self.dev_dataset = None
            self.evaluator = None

    async def prepare_triplet_data(self, triplets: list[Tuple[str, str, str]]) -> None:
        """
        Prepare data for triplet learning.

        Args:
            triplets: List of (anchor, positive, negative) text triplets
        """
        if not HAS_TORCH or not HAS_SENTENCE_TRANSFORMERS:
            self.logger.error("Required dependencies not installed")
            return

        train_examples = []

        # Process triplets
        for anchor, positive, negative in triplets:
            train_examples.append(InputExample(texts=[anchor, positive, negative]))

        # Split into train and dev
        train_test_split = self.config.training.train_test_split
        if train_test_split > 0:
            train_size = int(len(train_examples) * (1 - train_test_split))

            # Shuffle examples
            import random

            random.seed(self.config.training.random_seed)
            random.shuffle(train_examples)

            self.train_dataset = DomainDataset(train_examples[:train_size])
            self.dev_dataset = DomainDataset(train_examples[train_size:])

            # Creating evaluator from triplets requires conversion to similarity pairs
            dev_similarity_pairs = []
            for anchor, positive, negative in triplets[train_size:]:
                dev_similarity_pairs.append(
                    InputExample(texts=[anchor, positive], label=1.0)
                )
                dev_similarity_pairs.append(
                    InputExample(texts=[anchor, negative], label=0.0)
                )

            self.evaluator = EmbeddingSimilarityEvaluator.from_input_examples(
                dev_similarity_pairs, name=f"{self.config.domain}_dev"
            )
        else:
            self.train_dataset = DomainDataset(train_examples)
            self.dev_dataset = None
            self.evaluator = None

    async def prepare_supervised_data(
        self, text_pairs: list[Tuple[str, str]], similarity_scores: list[float]
    ) -> None:
        """
        Prepare data for supervised similarity learning.

        Args:
            text_pairs: List of (text1, text2) tuples
            similarity_scores: Corresponding similarity scores (0.0 to 1.0)
        """
        if not HAS_TORCH or not HAS_SENTENCE_TRANSFORMERS:
            self.logger.error("Required dependencies not installed")
            return

        train_examples = []

        # Process labeled pairs
        for (text1, text2), score in zip(text_pairs, similarity_scores):
            train_examples.append(
                InputExample(texts=[text1, text2], label=float(score))
            )

        # Split into train and dev
        train_test_split = self.config.training.train_test_split
        if train_test_split > 0:
            train_size = int(len(train_examples) * (1 - train_test_split))

            # Shuffle examples
            import random

            random.seed(self.config.training.random_seed)
            random.shuffle(train_examples)

            self.train_dataset = DomainDataset(train_examples[:train_size])
            self.dev_dataset = DomainDataset(train_examples[train_size:])

            # Create evaluator from dev set
            self.evaluator = EmbeddingSimilarityEvaluator.from_input_examples(
                train_examples[train_size:], name=f"{self.config.domain}_dev"
            )
        else:
            self.train_dataset = DomainDataset(train_examples)
            self.dev_dataset = None
            self.evaluator = None

    async def fine_tune(self) -> Dict[str, Any]:
        """
        Fine-tune the embedding model for the specific domain.

        Returns:
            Dictionary with training metrics and results
        """
        if not HAS_TORCH or not HAS_SENTENCE_TRANSFORMERS:
            self.logger.error("Required dependencies not installed")
            return {"error": "Required dependencies not installed"}

        if self.model is None:
            await self.initialize()

        if self.train_dataset is None:
            self.logger.error("Training data not prepared. Call prepare_*_data first.")
            return {"error": "Training data not prepared"}

        # Configure the training
        train_dataloader = DataLoader(
            self.train_dataset, batch_size=self.config.training.batch_size, shuffle=True
        )

        # Configure loss function based on fine-tuning method
        if self.config.method == FineTuningMethod.CONTRASTIVE:
            train_loss = losses.ContrastiveLoss(self.model)
        elif self.config.method == FineTuningMethod.TRIPLET:
            train_loss = losses.TripletLoss(self.model)
        elif self.config.method == FineTuningMethod.MULTIPLE_NEGATIVES:
            train_loss = losses.MultipleNegativesRankingLoss(self.model)
        elif self.config.method == FineTuningMethod.SUPERVISED:
            train_loss = losses.CosineSimilarityLoss(self.model)
        elif self.config.method == FineTuningMethod.DOMAIN_ADAPTATION:
            # In-domain and out-of-domain classifier with domain adversarial training
            train_loss = losses.SoftmaxLoss(
                self.model,
                sentence_embedding_dimension=self.model.get_sentence_embedding_dimension(),
                num_labels=2,  # In-domain vs. out-of-domain
            )
        elif self.config.method == FineTuningMethod.KNOWLEDGE_DISTILLATION:
            # This would require a teacher model, which we'll implement separately
            teacher_model_path = self.config.metadata.get("teacher_model")
            if not teacher_model_path:
                self.logger.error(
                    "Teacher model path required for knowledge distillation"
                )
                return {
                    "error": "Teacher model path required for knowledge distillation"
                }

            teacher_model = SentenceTransformer(teacher_model_path)
            train_loss = losses.MSELoss(model=self.model, teacher_model=teacher_model)
        else:
            self.logger.error(f"Unsupported fine-tuning method: {self.config.method}")
            return {"error": f"Unsupported fine-tuning method: {self.config.method}"}

        # Set up warmup steps
        warmup_steps = self.config.training.warmup_steps
        if warmup_steps <= 0:
            warmup_steps = int(
                len(train_dataloader) * self.config.training.num_epochs * 0.1
            )

        # Set up output directory
        output_path = os.path.join(
            self.config.output_dir, f"{self.config.domain}_model"
        )

        # Set up checkpoint saving
        checkpoint_path = self.config.training.checkpoint_path
        if not checkpoint_path:
            checkpoint_path = os.path.join(
                self.config.output_dir, f"{self.config.domain}_checkpoints"
            )
            os.makedirs(checkpoint_path, exist_ok=True)

        # Run the training
        self.logger.info(f"Starting fine-tuning for domain: {self.config.domain}")
        self.logger.info(f"Training examples: {len(self.train_dataset)}")
        if self.dev_dataset:
            self.logger.info(f"Dev examples: {len(self.dev_dataset)}")

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.model.fit(
                    train_objectives=[(train_dataloader, train_loss)],
                    evaluator=self.evaluator,
                    epochs=self.config.training.num_epochs,
                    evaluation_steps=self.config.training.evaluation_steps,
                    warmup_steps=warmup_steps,
                    output_path=output_path,
                    save_best_model=self.config.training.save_best_model,
                    checkpoint_path=checkpoint_path,
                    checkpoint_save_steps=self.config.training.checkpoint_save_steps,
                    optimizer_params={"lr": self.config.training.learning_rate},
                    use_amp=self.config.training.use_amp,
                ),
            )

            self.is_fine_tuned = True

            # Save config and metadata
            config_path = os.path.join(output_path, "adapter_config.json")
            with open(config_path, "w") as f:
                json.dump(self.config.dict(), f, indent=2)

            # Load the best model
            if self.config.training.save_best_model and os.path.exists(output_path):
                self.model = await loop.run_in_executor(
                    None, lambda: SentenceTransformer(output_path)
                )

            # Record evaluation results
            if self.evaluator:
                eval_result = self.evaluator(self.model)
                self.evaluation_results = {
                    "domain": self.config.domain,
                    "method": self.config.method,
                    "spearman_correlation": eval_result,
                    "num_examples": len(self.train_dataset),
                    "epochs": self.config.training.num_epochs,
                }

                # Save evaluation results
                eval_path = os.path.join(
                    self.config.output_dir, f"{self.config.domain}_eval.json"
                )
                with open(eval_path, "w") as f:
                    json.dump(self.evaluation_results, f, indent=2)

                return self.evaluation_results

            return {
                "domain": self.config.domain,
                "method": self.config.method,
                "status": "completed",
                "num_examples": len(self.train_dataset),
                "epochs": self.config.training.num_epochs,
            }

        except Exception as e:
            self.logger.error(f"Error during fine-tuning: {e}")
            return {"error": str(e)}

    async def evaluate(
        self,
        test_pairs: list[Tuple[str, str]],
        test_scores: list[float],
        batch_size: int = 32,
    ) -> Dict[str, float]:
        """
        Evaluate the model on a test set.

        Args:
            test_pairs: List of (text1, text2) tuples
            test_scores: Corresponding similarity scores (0.0 to 1.0)
            batch_size: Batch size for evaluation

        Returns:
            Dictionary with evaluation metrics
        """
        if not HAS_TORCH or not HAS_SENTENCE_TRANSFORMERS:
            self.logger.error("Required dependencies not installed")
            return {"error": "Required dependencies not installed"}

        if self.model is None:
            await self.initialize()

        # Create test examples
        test_examples = [
            InputExample(texts=[text1, text2], label=score)
            for (text1, text2), score in zip(test_pairs, test_scores)
        ]

        # Create evaluator
        test_evaluator = EmbeddingSimilarityEvaluator.from_input_examples(
            test_examples, name=f"{self.config.domain}_test", batch_size=batch_size
        )

        # Run evaluation
        try:
            loop = asyncio.get_event_loop()
            spearman_correlation = await loop.run_in_executor(
                None, lambda: test_evaluator(self.model)
            )

            results = {
                "spearman_correlation": spearman_correlation,
                "num_examples": len(test_examples),
            }

            # Save test results
            self.evaluation_results.update(
                {
                    "test_spearman_correlation": spearman_correlation,
                    "test_num_examples": len(test_examples),
                }
            )

            eval_path = os.path.join(
                self.config.output_dir, f"{self.config.domain}_eval.json"
            )
            with open(eval_path, "w") as f:
                json.dump(self.evaluation_results, f, indent=2)

            return results

        except Exception as e:
            self.logger.error(f"Error during evaluation: {e}")
            return {"error": str(e)}

    async def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a text string using the domain-adapted model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array
        """
        if self.model is None:
            await self.initialize()

        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, lambda: self.model.encode(text, convert_to_numpy=True)
            )
            return embedding

        except Exception as e:
            self.logger.error(f"Error embedding text: {e}")
            # Fall back to base model if fine-tuned model fails
            try:
                base_model = SentenceTransformer(self.config.base_model)
                return base_model.encode(text, convert_to_numpy=True)
            except Exception:
                # Return zeros as last resort
                return np.zeros(self.model.get_sentence_embedding_dimension())

    async def embed_batch(
        self, texts: list[str], batch_size: int = 32
    ) -> list[np.ndarray]:
        """
        Embed a batch of text strings using the domain-adapted model.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for embedding

        Returns:
            List of embedding vectors
        """
        if self.model is None:
            await self.initialize()

        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(
                    texts,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                ),
            )
            return embeddings

        except Exception as e:
            self.logger.error(f"Error embedding batch: {e}")
            # Fall back to individual embedding as last resort
            results = []
            for text in texts:
                embedding = await self.embed_text(text)
                results.append(embedding)
            return results

    async def compute_similarity(
        self, text1: str, text2: str, method: str = "cosine"
    ) -> float:
        """
        Compute similarity between two texts using the domain-adapted model.

        Args:
            text1: First text
            text2: Second text
            method: Similarity method (cosine, dot, euclidean)

        Returns:
            Similarity score (higher means more similar)
        """
        embedding1 = await self.embed_text(text1)
        embedding2 = await self.embed_text(text2)

        if method == "cosine":
            from sklearn.metrics.pairwise import cosine_similarity

            return float(cosine_similarity([embedding1], [embedding2])[0][0])
        elif method == "dot":
            return float(np.dot(embedding1, embedding2))
        elif method == "euclidean":
            from sklearn.metrics.pairwise import euclidean_distances

            distance = euclidean_distances([embedding1], [embedding2])[0][0]
            return float(1.0 / (1.0 + distance))  # Convert to similarity
        else:
            raise ValueError(f"Unsupported similarity method: {method}")

    async def export_model(self, export_path: str | None = None) -> str:
        """
        Export the fine-tuned model for deployment.

        Args:
            export_path: Path to export the model (defaults to output_dir/domain_export)

        Returns:
            Path to exported model
        """
        if self.model is None:
            await self.initialize()

        if not export_path:
            export_path = os.path.join(
                self.config.output_dir, f"{self.config.domain}_export"
            )

        os.makedirs(export_path, exist_ok=True)

        # Save the model
        self.model.save(export_path)

        # Save the config
        config_path = os.path.join(export_path, "adapter_config.json")
        with open(config_path, "w") as f:
            json.dump(self.config.dict(), f, indent=2)

        # Save evaluation results if available
        if self.evaluation_results:
            eval_path = os.path.join(export_path, "evaluation_results.json")
            with open(eval_path, "w") as f:
                json.dump(self.evaluation_results, f, indent=2)

        return export_path

    async def close(self):
        """Release resources."""
        pass  # No specific resources to release for this adapter


# Factory function for domain embedding adapters
async def create_domain_embedding_adapter(
    domain: str,
    base_model: str = "all-MiniLM-L6-v2",
    method: Union[str, FineTuningMethod] = FineTuningMethod.CONTRASTIVE,
    output_dir: str = "./domain_models",
    logger: logging.Logger | None = None,
) -> DomainEmbeddingAdapter:
    """
    Create a domain embedding adapter for a specific domain.

    Args:
        domain: Domain name (e.g., "healthcare", "legal", "finance")
        base_model: Base model name
        method: Fine-tuning method
        output_dir: Output directory for models
        logger: Optional logger

    Returns:
        Initialized domain embedding adapter
    """
    if isinstance(method, str):
        method = FineTuningMethod(method)

    config = EmbeddingAdapterConfig(
        base_model=base_model,
        domain=domain,
        method=method,
        output_dir=output_dir,
        description=f"Domain-adapted embedding model for {domain}",
    )

    adapter = DomainEmbeddingAdapter(config, logger=logger)
    await adapter.initialize()

    return adapter
