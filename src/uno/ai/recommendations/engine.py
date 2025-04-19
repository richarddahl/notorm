"""
Recommendation engine core implementation.

This module provides the base recommendation engine infrastructure
with support for different recommendation algorithms and strategies.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Type, TypeVar, Generic, Set
from datetime import datetime, timedelta, UTC

import numpy as np

from uno.ai.embeddings import EmbeddingModel, get_embedding_model
from uno.ai.vector_storage import VectorStorage, create_vector_storage

# Set up logger
logger = logging.getLogger(__name__)

# Type variable for item IDs
T = TypeVar('T')


class RecommendationAlgorithm(Generic[T], ABC):
    """Base class for recommendation algorithms."""
    
    @abstractmethod
    async def train(self, interactions: List[Dict[str, Any]]) -> None:
        """
        Train the recommendation algorithm on interaction data.
        
        Args:
            interactions: List of user-item interactions
        """
        pass
    
    @abstractmethod
    async def recommend(
        self, 
        user_id: str, 
        limit: int = 10,
        exclusions: Optional[List[T]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a user.
        
        Args:
            user_id: ID of the user to generate recommendations for
            limit: Maximum number of recommendations to generate
            exclusions: Optional list of item IDs to exclude
            
        Returns:
            List of recommended items with scores
        """
        pass
    
    @abstractmethod
    async def add_interaction(self, interaction: Dict[str, Any]) -> None:
        """
        Add a single interaction to the algorithm.
        
        Args:
            interaction: User-item interaction data
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Clean up resources used by the algorithm."""
        pass


class ContentBasedRecommender(RecommendationAlgorithm[T]):
    """
    Content-based recommendation algorithm using item embeddings.
    
    Recommends items similar to those a user has interacted with.
    """
    
    def __init__(
        self,
        embedding_model: Union[str, EmbeddingModel] = "default",
        vector_storage: Optional[VectorStorage] = None,
        connection_string: Optional[str] = None,
        storage_type: str = "pgvector",
        table_name: str = "recommendation_embeddings",
        schema: str = "public",
        interaction_weights: Optional[Dict[str, float]] = None,
        item_id_field: str = "item_id",
        item_type_field: str = "item_type",
        user_id_field: str = "user_id",
        interaction_type_field: str = "interaction_type",
        item_content_field: str = "content",
        timestamp_field: str = "timestamp"
    ):
        """
        Initialize the content-based recommender.
        
        Args:
            embedding_model: Embedding model or name of registered model
            vector_storage: Vector storage instance (optional)
            connection_string: Database connection string (if no storage provided)
            storage_type: Type of vector storage to create (if no storage provided)
            table_name: Table name for storage (if no storage provided)
            schema: Database schema (if no storage provided)
            interaction_weights: Weights for different interaction types (default: {"view": 1.0, "like": 2.0, "purchase": 3.0})
            item_id_field: Field name for item ID in interactions
            item_type_field: Field name for item type in interactions
            user_id_field: Field name for user ID in interactions
            interaction_type_field: Field name for interaction type in interactions
            item_content_field: Field name for item content in interactions
            timestamp_field: Field name for timestamp in interactions
        """
        # Set up embedding model
        if isinstance(embedding_model, str):
            self.embedding_model = get_embedding_model(embedding_model)
        else:
            self.embedding_model = embedding_model
        
        # Set up vector storage
        self.vector_storage = vector_storage
        self._storage_params = {}
        
        if vector_storage is None:
            if connection_string is None:
                raise ValueError(
                    "Either vector_storage or connection_string must be provided"
                )
            
            # Store params for lazy initialization
            self._storage_params = {
                "storage_type": storage_type,
                "connection_string": connection_string,
                "table_name": table_name,
                "dimensions": self.embedding_model.dimensions,
                "schema": schema
            }
        
        # Set up field mappings
        self.item_id_field = item_id_field
        self.item_type_field = item_type_field
        self.user_id_field = user_id_field
        self.interaction_type_field = interaction_type_field
        self.item_content_field = item_content_field
        self.timestamp_field = timestamp_field
        
        # Set up interaction weights
        self.interaction_weights = interaction_weights or {
            "view": 1.0,
            "like": 2.0,
            "purchase": 3.0
        }
        
        # User profile cache
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.user_interactions: Dict[str, Dict[T, Dict[str, Any]]] = {}
        
        # Item cache
        self.item_cache: Dict[T, Dict[str, Any]] = {}
        
        # Initialization state
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the recommender."""
        if self.initialized:
            return
            
        # Create vector storage if needed
        if self.vector_storage is None:
            self.vector_storage = await create_vector_storage(**self._storage_params)
        
        self.initialized = True
        logger.info(
            f"Initialized ContentBasedRecommender with model {self.embedding_model.model_name} "
            f"({self.embedding_model.dimensions} dimensions)"
        )
    
    async def train(self, interactions: List[Dict[str, Any]]) -> None:
        """
        Train the recommendation algorithm on interaction data.
        
        Args:
            interactions: List of user-item interactions
        """
        if not self.initialized:
            await self.initialize()
        
        # Process all interactions
        for interaction in interactions:
            await self.add_interaction(interaction)
        
        # Update user profiles
        await self._update_user_profiles()
        
        logger.info(f"Trained ContentBasedRecommender on {len(interactions)} interactions")
    
    async def add_interaction(self, interaction: Dict[str, Any]) -> None:
        """
        Add a single interaction to the algorithm.
        
        Args:
            interaction: User-item interaction data
        """
        if not self.initialized:
            await self.initialize()
        
        # Extract fields
        user_id = interaction[self.user_id_field]
        item_id = interaction[self.item_id_field]
        item_type = interaction.get(self.item_type_field, "item")
        interaction_type = interaction.get(self.interaction_type_field, "view")
        content = interaction.get(self.item_content_field)
        timestamp = interaction.get(
            self.timestamp_field, 
            datetime.now(datetime.UTC).isoformat()
        )
        
        # Create user entry if not exists
        if user_id not in self.user_interactions:
            self.user_interactions[user_id] = {}
        
        # Add interaction to user history
        self.user_interactions[user_id][item_id] = {
            "item_id": item_id,
            "item_type": item_type,
            "interaction_type": interaction_type,
            "timestamp": timestamp,
            "weight": self.interaction_weights.get(interaction_type, 1.0)
        }
        
        # Index item content if provided
        if content:
            # Cache item content
            self.item_cache[item_id] = {
                "item_id": item_id,
                "item_type": item_type,
                "content": content
            }
            
            # Generate embedding
            embedding = self.embedding_model.embed(content)
            
            # Store in vector database
            await self.vector_storage.store(
                entity_id=str(item_id),
                entity_type=item_type,
                embedding=embedding,
                metadata={
                    "item_id": str(item_id),
                    "item_type": item_type
                }
            )
    
    async def _update_user_profiles(self) -> None:
        """Update user profiles based on interactions."""
        for user_id, interactions in self.user_interactions.items():
            # Skip if no interactions
            if not interactions:
                continue
                
            # Compute weighted profile
            items = []
            weights = []
            
            for item_id, interaction in interactions.items():
                # Skip if item not in cache
                if item_id not in self.item_cache:
                    continue
                    
                # Get item content
                content = self.item_cache[item_id].get("content")
                if not content:
                    continue
                
                # Add to lists
                items.append(content)
                weights.append(interaction["weight"])
            
            # Skip if no valid items
            if not items:
                continue
                
            # Normalize weights
            weights = np.array(weights)
            weights = weights / weights.sum()
            
            # Generate embeddings
            embeddings = self.embedding_model.embed_batch(items)
            
            # Compute weighted average
            profile_embedding = np.average(embeddings, axis=0, weights=weights)
            
            # Normalize embedding
            profile_embedding = profile_embedding / np.linalg.norm(profile_embedding)
            
            # Store user profile
            self.user_profiles[user_id] = {
                "embedding": profile_embedding,
                "updated_at": datetime.now(datetime.UTC).isoformat()
            }
    
    async def recommend(
        self, 
        user_id: str, 
        limit: int = 10,
        exclusions: Optional[List[T]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a user.
        
        Args:
            user_id: ID of the user to generate recommendations for
            limit: Maximum number of recommendations to generate
            exclusions: Optional list of item IDs to exclude
            
        Returns:
            List of recommended items with scores
        """
        if not self.initialized:
            await self.initialize()
        
        # Set default exclusions if not provided
        if exclusions is None:
            exclusions = []
        
        # Add items user has already interacted with to exclusions
        if user_id in self.user_interactions:
            exclusions.extend(list(self.user_interactions[user_id].keys()))
        
        # Convert exclusions to strings for comparison
        exclusions_set = {str(item_id) for item_id in exclusions}
        
        # Get user profile
        profile = self.user_profiles.get(user_id)
        if not profile:
            # If no profile, return empty list
            logger.warning(f"No profile found for user {user_id}")
            return []
        
        # Get profile embedding
        profile_embedding = profile["embedding"]
        
        # Search for similar items
        results = await self.vector_storage.search(
            query_embedding=profile_embedding,
            limit=limit * 2,  # Get more than needed to allow for filtering
            similarity_threshold=0.5
        )
        
        # Filter out exclusions
        filtered_results = []
        for result in results:
            item_id = result["entity_id"]
            
            # Skip if in exclusions
            if item_id in exclusions_set:
                continue
                
            filtered_results.append({
                "item_id": item_id,
                "item_type": result["entity_type"],
                "score": float(result["similarity"]),
                "metadata": result["metadata"]
            })
            
            # Stop if we have enough
            if len(filtered_results) >= limit:
                break
        
        logger.debug(f"Generated {len(filtered_results)} recommendations for user {user_id}")
        return filtered_results
    
    async def close(self) -> None:
        """Clean up resources used by the algorithm."""
        if self.vector_storage:
            await self.vector_storage.close()
        
        self.initialized = False


class CollaborativeFilteringRecommender(RecommendationAlgorithm[T]):
    """
    Collaborative filtering recommendation algorithm.
    
    Finds patterns in user-item interactions to recommend items
    that users with similar preferences have liked.
    """
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        item_id_field: str = "item_id",
        item_type_field: str = "item_type",
        user_id_field: str = "user_id",
        interaction_type_field: str = "interaction_type",
        rating_field: str = "rating",
        timestamp_field: str = "timestamp",
        interaction_weights: Optional[Dict[str, float]] = None,
        implicit_ratings: bool = True,
        use_timestamps: bool = True,
        time_decay_factor: float = 0.1,
        min_interactions: int = 5
    ):
        """
        Initialize the collaborative filtering recommender.
        
        Args:
            connection_string: Database connection string (optional)
            item_id_field: Field name for item ID in interactions
            item_type_field: Field name for item type in interactions
            user_id_field: Field name for user ID in interactions
            interaction_type_field: Field name for interaction type in interactions
            rating_field: Field name for rating in interactions
            timestamp_field: Field name for timestamp in interactions
            interaction_weights: Weights for different interaction types
            implicit_ratings: Whether to use implicit ratings from interactions
            use_timestamps: Whether to use timestamps for time decay
            time_decay_factor: Factor for time decay (0 = no decay, higher = more decay)
            min_interactions: Minimum interactions for recommendations
        """
        self.connection_string = connection_string
        
        # Set up field mappings
        self.item_id_field = item_id_field
        self.item_type_field = item_type_field
        self.user_id_field = user_id_field
        self.interaction_type_field = interaction_type_field
        self.rating_field = rating_field
        self.timestamp_field = timestamp_field
        
        # Set up interaction weights
        self.interaction_weights = interaction_weights or {
            "view": 1.0,
            "like": 3.0,
            "purchase": 5.0,
            "rate": 5.0
        }
        
        # Configuration
        self.implicit_ratings = implicit_ratings
        self.use_timestamps = use_timestamps
        self.time_decay_factor = time_decay_factor
        self.min_interactions = min_interactions
        
        # User-item matrix (sparse representation)
        self.user_items: Dict[str, Dict[T, float]] = {}
        self.item_users: Dict[T, Dict[str, float]] = {}
        
        # Metadata
        self.item_metadata: Dict[T, Dict[str, Any]] = {}
        self.user_metadata: Dict[str, Dict[str, Any]] = {}
        
        # User similarity cache
        self.user_similarity: Dict[str, Dict[str, float]] = {}
        
        # Timestamp information
        self.latest_timestamp = datetime.min
        
        # Initialization state
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the recommender."""
        if self.initialized:
            return
        
        self.initialized = True
        logger.info("Initialized CollaborativeFilteringRecommender")
    
    async def train(self, interactions: List[Dict[str, Any]]) -> None:
        """
        Train the recommendation algorithm on interaction data.
        
        Args:
            interactions: List of user-item interactions
        """
        if not self.initialized:
            await self.initialize()
        
        # Process all interactions
        for interaction in interactions:
            await self.add_interaction(interaction)
        
        # Update similarity matrix
        await self._update_similarity_matrix()
        
        logger.info(f"Trained CollaborativeFilteringRecommender on {len(interactions)} interactions")
    
    async def add_interaction(self, interaction: Dict[str, Any]) -> None:
        """
        Add a single interaction to the algorithm.
        
        Args:
            interaction: User-item interaction data
        """
        if not self.initialized:
            await self.initialize()
        
        # Extract fields
        user_id = interaction[self.user_id_field]
        item_id = interaction[self.item_id_field]
        item_type = interaction.get(self.item_type_field, "item")
        interaction_type = interaction.get(self.interaction_type_field, "view")
        
        # Get rating (explicit or implicit)
        if self.rating_field in interaction and not self.implicit_ratings:
            rating = float(interaction[self.rating_field])
        else:
            # Use interaction weight as implicit rating
            rating = self.interaction_weights.get(interaction_type, 1.0)
        
        # Process timestamp if available
        timestamp_str = interaction.get(self.timestamp_field)
        if timestamp_str and self.use_timestamps:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                
                # Update latest timestamp
                if timestamp > self.latest_timestamp:
                    self.latest_timestamp = timestamp
                    
                # Store timestamp in metadata
                if user_id not in self.user_metadata:
                    self.user_metadata[user_id] = {}
                if item_id not in self.user_metadata[user_id]:
                    self.user_metadata[user_id][item_id] = {}
                
                self.user_metadata[user_id][item_id]["timestamp"] = timestamp
            except (ValueError, TypeError):
                # Invalid timestamp format
                pass
        
        # Update user-item matrix
        if user_id not in self.user_items:
            self.user_items[user_id] = {}
        
        # Store highest rating if multiple interactions
        if item_id in self.user_items[user_id]:
            self.user_items[user_id][item_id] = max(
                self.user_items[user_id][item_id],
                rating
            )
        else:
            self.user_items[user_id][item_id] = rating
        
        # Update item-user matrix
        if item_id not in self.item_users:
            self.item_users[item_id] = {}
        
        # Store highest rating if multiple interactions
        if user_id in self.item_users[item_id]:
            self.item_users[item_id][user_id] = max(
                self.item_users[item_id][user_id],
                rating
            )
        else:
            self.item_users[item_id][user_id] = rating
        
        # Store item metadata
        if item_id not in self.item_metadata:
            self.item_metadata[item_id] = {
                "item_id": item_id,
                "item_type": item_type
            }
    
    async def _update_similarity_matrix(self) -> None:
        """Update user similarity matrix."""
        # Reset similarity matrix
        self.user_similarity = {}
        
        # Find users with sufficient interactions
        valid_users = [
            user_id for user_id, items in self.user_items.items()
            if len(items) >= self.min_interactions
        ]
        
        # Skip if not enough users
        if len(valid_users) < 2:
            logger.warning("Not enough users with interactions for similarity calculation")
            return
        
        # Calculate similarity for each pair of users
        for i, user1 in enumerate(valid_users):
            if user1 not in self.user_similarity:
                self.user_similarity[user1] = {}
                
            for user2 in valid_users[i+1:]:
                if user2 not in self.user_similarity:
                    self.user_similarity[user2] = {}
                
                # Calculate similarity
                similarity = self._calculate_similarity(user1, user2)
                
                # Store in both directions
                self.user_similarity[user1][user2] = similarity
                self.user_similarity[user2][user1] = similarity
        
        logger.debug(f"Updated similarity matrix for {len(valid_users)} users")
    
    def _calculate_similarity(self, user1: str, user2: str) -> float:
        """
        Calculate cosine similarity between two users.
        
        Args:
            user1: First user ID
            user2: Second user ID
            
        Returns:
            Similarity score (0-1)
        """
        # Get user items
        items1 = self.user_items[user1]
        items2 = self.user_items[user2]
        
        # Find common items
        common_items = set(items1.keys()) & set(items2.keys())
        
        # If no common items, similarity is 0
        if not common_items:
            return 0.0
        
        # Calculate vector magnitudes and dot product
        dot_product = 0.0
        magnitude1 = 0.0
        magnitude2 = 0.0
        
        for item_id in set(items1.keys()) | set(items2.keys()):
            rating1 = items1.get(item_id, 0.0)
            rating2 = items2.get(item_id, 0.0)
            
            # Apply time decay if enabled
            if self.use_timestamps and self.latest_timestamp != datetime.min:
                if (user1 in self.user_metadata and 
                        item_id in self.user_metadata[user1] and
                        "timestamp" in self.user_metadata[user1][item_id]):
                    timestamp1 = self.user_metadata[user1][item_id]["timestamp"]
                    time_diff = (self.latest_timestamp - timestamp1).total_seconds() / 86400.0  # days
                    decay = np.exp(-self.time_decay_factor * time_diff)
                    rating1 *= decay
                
                if (user2 in self.user_metadata and 
                        item_id in self.user_metadata[user2] and
                        "timestamp" in self.user_metadata[user2][item_id]):
                    timestamp2 = self.user_metadata[user2][item_id]["timestamp"]
                    time_diff = (self.latest_timestamp - timestamp2).total_seconds() / 86400.0  # days
                    decay = np.exp(-self.time_decay_factor * time_diff)
                    rating2 *= decay
            
            # Update dot product and magnitudes
            if item_id in common_items:
                dot_product += rating1 * rating2
            
            magnitude1 += rating1 ** 2
            magnitude2 += rating2 ** 2
        
        # Calculate cosine similarity
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
            
        similarity = dot_product / (np.sqrt(magnitude1) * np.sqrt(magnitude2))
        
        return similarity
    
    async def recommend(
        self, 
        user_id: str, 
        limit: int = 10,
        exclusions: Optional[List[T]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a user.
        
        Args:
            user_id: ID of the user to generate recommendations for
            limit: Maximum number of recommendations to generate
            exclusions: Optional list of item IDs to exclude
            
        Returns:
            List of recommended items with scores
        """
        if not self.initialized:
            await self.initialize()
        
        # Set default exclusions if not provided
        if exclusions is None:
            exclusions = []
        
        # Convert exclusions to set for faster lookup
        exclusions_set = set(exclusions)
        
        # Add items user has already interacted with to exclusions
        if user_id in self.user_items:
            exclusions_set.update(self.user_items[user_id].keys())
        
        # If user has no interactions, return empty list
        if user_id not in self.user_items or user_id not in self.user_similarity:
            logger.warning(f"User {user_id} has no interactions or similarity data")
            return []
        
        # Find similar users
        similar_users = sorted(
            self.user_similarity[user_id].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Limit to top N similar users
        top_n = 20
        similar_users = similar_users[:top_n]
        
        # Calculate item scores
        item_scores: Dict[T, float] = {}
        
        for similar_user, similarity in similar_users:
            # Skip if similarity is too low
            if similarity < 0.1:
                continue
                
            # Get items rated by similar user
            for item_id, rating in self.user_items[similar_user].items():
                # Skip if in exclusions
                if item_id in exclusions_set:
                    continue
                    
                # Calculate weighted score
                weighted_score = similarity * rating
                
                # Add to item scores
                if item_id in item_scores:
                    item_scores[item_id] += weighted_score
                else:
                    item_scores[item_id] = weighted_score
        
        # Sort items by score
        recommendations = sorted(
            [
                {
                    "item_id": item_id,
                    "score": score,
                    "item_type": self.item_metadata.get(item_id, {}).get("item_type", "item")
                }
                for item_id, score in item_scores.items()
            ],
            key=lambda x: x["score"],
            reverse=True
        )
        
        # Limit to requested number
        recommendations = recommendations[:limit]
        
        logger.debug(f"Generated {len(recommendations)} recommendations for user {user_id}")
        return recommendations
    
    async def close(self) -> None:
        """Clean up resources used by the algorithm."""
        self.initialized = False


class HybridRecommender(RecommendationAlgorithm[T]):
    """
    Hybrid recommendation algorithm combining multiple approaches.
    
    Combines the strengths of different recommendation algorithms
    to provide more robust and diverse recommendations.
    """
    
    def __init__(
        self,
        algorithms: List[RecommendationAlgorithm[T]],
        weights: Optional[List[float]] = None,
        diversification_factor: float = 0.3
    ):
        """
        Initialize the hybrid recommender.
        
        Args:
            algorithms: List of recommendation algorithms to combine
            weights: Optional weights for each algorithm (default: equal weights)
            diversification_factor: Factor for result diversification (0-1)
        """
        self.algorithms = algorithms
        
        # Set default weights if not provided
        if weights is None:
            self.weights = [1.0 / len(algorithms)] * len(algorithms)
        else:
            # Normalize weights
            total = sum(weights)
            self.weights = [w / total for w in weights]
        
        # Ensure weights and algorithms have same length
        if len(self.weights) != len(algorithms):
            raise ValueError("Number of weights must match number of algorithms")
        
        self.diversification_factor = diversification_factor
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the recommender."""
        if self.initialized:
            return
        
        # Initialize all algorithms
        for algorithm in self.algorithms:
            await algorithm.initialize()
        
        self.initialized = True
        logger.info(f"Initialized HybridRecommender with {len(self.algorithms)} algorithms")
    
    async def train(self, interactions: List[Dict[str, Any]]) -> None:
        """
        Train the recommendation algorithm on interaction data.
        
        Args:
            interactions: List of user-item interactions
        """
        if not self.initialized:
            await self.initialize()
        
        # Train all algorithms
        for algorithm in self.algorithms:
            await algorithm.train(interactions)
        
        logger.info(f"Trained HybridRecommender on {len(interactions)} interactions")
    
    async def add_interaction(self, interaction: Dict[str, Any]) -> None:
        """
        Add a single interaction to the algorithm.
        
        Args:
            interaction: User-item interaction data
        """
        if not self.initialized:
            await self.initialize()
        
        # Add to all algorithms
        for algorithm in self.algorithms:
            await algorithm.add_interaction(interaction)
    
    async def recommend(
        self, 
        user_id: str, 
        limit: int = 10,
        exclusions: Optional[List[T]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a user.
        
        Args:
            user_id: ID of the user to generate recommendations for
            limit: Maximum number of recommendations to generate
            exclusions: Optional list of item IDs to exclude
            
        Returns:
            List of recommended items with scores
        """
        if not self.initialized:
            await self.initialize()
        
        # Set default exclusions if not provided
        if exclusions is None:
            exclusions = []
        
        # Get recommendations from each algorithm
        all_recommendations = []
        
        for i, algorithm in enumerate(self.algorithms):
            try:
                # Get more recommendations than needed for diversity
                algo_limit = int(limit * (1 + self.diversification_factor))
                
                # Get recommendations
                recommendations = await algorithm.recommend(
                    user_id=user_id,
                    limit=algo_limit,
                    exclusions=exclusions
                )
                
                # Apply weight to scores
                weight = self.weights[i]
                for rec in recommendations:
                    rec["score"] *= weight
                    rec["source"] = i  # Track source algorithm
                
                all_recommendations.extend(recommendations)
            except Exception as e:
                logger.error(f"Error getting recommendations from algorithm {i}: {str(e)}")
        
        # Combine and deduplicate
        combined: Dict[str, Dict[str, Any]] = {}
        
        for rec in all_recommendations:
            item_id = rec["item_id"]
            
            if item_id in combined:
                # Update existing recommendation
                combined[item_id]["score"] += rec["score"]
                combined[item_id]["sources"].add(rec["source"])
            else:
                # Add new recommendation
                combined[item_id] = {
                    "item_id": item_id,
                    "item_type": rec["item_type"],
                    "score": rec["score"],
                    "sources": {rec["source"]}
                }
                
                # Copy additional fields
                for key, value in rec.items():
                    if key not in ["item_id", "item_type", "score", "source", "sources"]:
                        combined[item_id][key] = value
        
        # Sort by score
        recommendations = sorted(
            combined.values(),
            key=lambda x: x["score"],
            reverse=True
        )
        
        # Apply diversification
        if self.diversification_factor > 0:
            recommendations = self._diversify_results(recommendations)
        
        # Limit to requested number
        recommendations = recommendations[:limit]
        
        # Convert sources set to list for serialization
        for rec in recommendations:
            rec["sources"] = list(rec["sources"])
        
        logger.debug(f"Generated {len(recommendations)} hybrid recommendations for user {user_id}")
        return recommendations
    
    def _diversify_results(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Diversify recommendation results.
        
        Args:
            recommendations: List of recommendations
            
        Returns:
            Diversified list of recommendations
        """
        # If too few recommendations, return as is
        if len(recommendations) < 2:
            return recommendations
            
        # Use a greedy algorithm to maximize diversity while maintaining relevance
        result = [recommendations[0]]  # Start with top recommendation
        remaining = recommendations[1:]
        
        # Set of item types already included
        included_types = {result[0]["item_type"]}
        
        while remaining and len(result) < len(recommendations):
            # Score remaining recommendations by diversity and relevance
            best_score = -1
            best_idx = -1
            
            for i, rec in enumerate(remaining):
                # Base score is recommendation score
                score = rec["score"]
                
                # Bonus for new item type
                if rec["item_type"] not in included_types:
                    score *= (1 + self.diversification_factor)
                
                # Bonus for multiple sources
                source_count = len(rec["sources"])
                if source_count > 1:
                    score *= (1 + (source_count - 1) * 0.1)
                
                # Update best
                if score > best_score:
                    best_score = score
                    best_idx = i
            
            # Add best recommendation to result
            if best_idx >= 0:
                best_rec = remaining.pop(best_idx)
                result.append(best_rec)
                included_types.add(best_rec["item_type"])
        
        return result
    
    async def close(self) -> None:
        """Clean up resources used by the algorithm."""
        # Close all algorithms
        for algorithm in self.algorithms:
            await algorithm.close()
        
        self.initialized = False


class RecommendationEngine(Generic[T]):
    """
    Recommendation engine that manages recommendation algorithms.
    
    This is the main entry point for the recommendation system,
    providing high-level methods for generating recommendations.
    """
    
    def __init__(
        self,
        algorithm: Optional[RecommendationAlgorithm[T]] = None,
        connection_string: Optional[str] = None,
        embedding_model: str = "default"
    ):
        """
        Initialize the recommendation engine.
        
        Args:
            algorithm: Recommendation algorithm to use (default: creates a hybrid recommender)
            connection_string: Database connection string for storage
            embedding_model: Embedding model name for content-based recommendations
        """
        self.algorithm = algorithm
        self.connection_string = connection_string
        self.embedding_model = embedding_model
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the recommendation engine."""
        if self.initialized:
            return
            
        # Create default algorithm if not provided
        if self.algorithm is None:
            if not self.connection_string:
                raise ValueError(
                    "Either algorithm or connection_string must be provided"
                )
                
            # Create content-based recommender
            content_recommender = ContentBasedRecommender(
                embedding_model=self.embedding_model,
                connection_string=self.connection_string,
                table_name="recommendation_content_embeddings"
            )
            
            # Create collaborative filtering recommender
            collab_recommender = CollaborativeFilteringRecommender()
            
            # Create hybrid recommender
            self.algorithm = HybridRecommender(
                algorithms=[content_recommender, collab_recommender],
                weights=[0.6, 0.4]  # Higher weight for content-based
            )
        
        # Initialize algorithm
        await self.algorithm.initialize()
        
        self.initialized = True
        logger.info("Initialized RecommendationEngine")
    
    async def train(self, interactions: List[Dict[str, Any]]) -> None:
        """
        Train the recommendation engine on interaction data.
        
        Args:
            interactions: List of user-item interactions
        """
        if not self.initialized:
            await self.initialize()
        
        await self.algorithm.train(interactions)
    
    async def add_interaction(self, interaction: Dict[str, Any]) -> None:
        """
        Add a single interaction to the recommendation engine.
        
        Args:
            interaction: User-item interaction data
        """
        if not self.initialized:
            await self.initialize()
        
        await self.algorithm.add_interaction(interaction)
    
    async def recommend(
        self, 
        user_id: str, 
        limit: int = 10,
        exclusions: Optional[List[T]] = None,
        item_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a user.
        
        Args:
            user_id: ID of the user to generate recommendations for
            limit: Maximum number of recommendations to generate
            exclusions: Optional list of item IDs to exclude
            item_type: Optional filter by item type
            
        Returns:
            List of recommended items with scores
        """
        if not self.initialized:
            await self.initialize()
        
        # Get recommendations
        recommendations = await self.algorithm.recommend(
            user_id=user_id,
            limit=limit * 2 if item_type else limit,  # Get more if filtering
            exclusions=exclusions
        )
        
        # Filter by item type if specified
        if item_type:
            recommendations = [
                rec for rec in recommendations
                if rec.get("item_type") == item_type
            ][:limit]
        
        return recommendations
    
    async def close(self) -> None:
        """Close the recommendation engine."""
        if self.algorithm:
            await self.algorithm.close()
        
        self.initialized = False