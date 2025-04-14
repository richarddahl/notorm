"""
Automated knowledge graph construction from text.

This module provides functionality to extract entities and relationships from text
and automatically construct a knowledge graph based on the extracted information.
"""

import asyncio
import json
import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import asyncpg
from pydantic import BaseModel, Field, validator

# Optional imports for different extraction methods
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class EntityExtractionMethod(str, Enum):
    """Method for extracting entities from text."""
    
    RULE_BASED = "rule_based"
    SPACY_NER = "spacy_ner"
    TRANSFORMER_NER = "transformer_ner"
    CUSTOM = "custom"


class RelationshipExtractionMethod(str, Enum):
    """Method for extracting relationships from text."""
    
    PATTERN_BASED = "pattern_based"
    DEPENDENCY_PARSING = "dependency_parsing"
    TRANSFORMER_RE = "transformer_re"
    CUSTOM = "custom"


class ValidationMethod(str, Enum):
    """Method for validating extracted knowledge."""
    
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    CROSS_REFERENCE = "cross_reference"
    HUMAN_IN_LOOP = "human_in_loop"
    NONE = "none"


class TextSource(BaseModel):
    """Source of text for knowledge extraction."""
    
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_type: str = "document"
    source_url: Optional[str] = None
    timestamp: Optional[str] = None


class Entity(BaseModel):
    """An entity extracted from text."""
    
    id: str
    text: str
    type: str
    start_char: int
    end_char: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_id: Optional[str] = None


class Relationship(BaseModel):
    """A relationship between entities."""
    
    id: str
    source_entity_id: str
    target_entity_id: str
    type: str
    text: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_id: Optional[str] = None


class Triple(BaseModel):
    """A knowledge triple (subject-predicate-object)."""
    
    subject: Entity
    predicate: str
    object: Entity
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_id: Optional[str] = None


class ConstructionPipeline(BaseModel):
    """Configuration for the knowledge graph construction pipeline."""
    
    entity_extraction_method: EntityExtractionMethod = EntityExtractionMethod.SPACY_NER
    relationship_extraction_method: RelationshipExtractionMethod = RelationshipExtractionMethod.DEPENDENCY_PARSING
    validation_method: ValidationMethod = ValidationMethod.CONFIDENCE_THRESHOLD
    entity_confidence_threshold: float = 0.5
    relationship_confidence_threshold: float = 0.7
    entity_types: List[str] = Field(default_factory=list)
    relationship_types: List[str] = Field(default_factory=list)
    merge_similar_entities: bool = True
    similarity_threshold: float = 0.85
    max_token_length: int = 512
    batch_size: int = 10
    model_name: Optional[str] = None


class KnowledgeConstructorConfig(BaseModel):
    """Configuration for knowledge constructor."""
    
    age_schema: str = "ag_catalog"
    graph_name: str = "knowledge_graph"
    default_pipeline: ConstructionPipeline = Field(default_factory=ConstructionPipeline)
    custom_entity_patterns: Dict[str, List[str]] = Field(default_factory=dict)
    custom_relationship_patterns: Dict[str, List[str]] = Field(default_factory=dict)
    spacy_model: str = "en_core_web_sm"
    transformer_model: str = "dslim/bert-base-NER"
    create_node_properties: bool = True
    create_relationship_properties: bool = True
    auto_generate_embeddings: bool = False
    embedding_model: Optional[str] = None
    deduplication_enabled: bool = True
    validation_enabled: bool = True
    max_batch_size: int = 1000
    cache_results: bool = True
    cache_ttl: int = 3600  # seconds
    timeout: int = 60  # seconds


class ExtractionResult(BaseModel):
    """Result of knowledge extraction from text."""
    
    source_id: str
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    triples: List[Triple] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConstructionResult(BaseModel):
    """Result of knowledge graph construction."""
    
    construction_id: str
    source_ids: List[str] = Field(default_factory=list)
    entity_count: int = 0
    relationship_count: int = 0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeConstructor:
    """
    Automated knowledge graph construction from text.
    
    This class provides functionality to extract entities and relationships from text
    and automatically construct a knowledge graph based on the extracted information.
    """
    
    def __init__(
        self,
        connection_string: str,
        config: KnowledgeConstructorConfig,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the knowledge constructor.
        
        Args:
            connection_string: Database connection string
            config: Configuration for knowledge constructor
            logger: Optional logger
        """
        self.connection_string = connection_string
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Database connection
        self.pool = None
        
        # NLP components
        self.spacy_nlp = None
        self.transformer_ner = None
        self.transformer_re = None
        
        # Entity and relationship patterns
        self.entity_patterns = {}
        self.relationship_patterns = {}
        
        # Cache for extracted knowledge
        self.extraction_cache = {}
        self.cache_timestamps = {}
        
        # Initialization flag
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the knowledge constructor."""
        if self.initialized:
            return
        
        try:
            # Initialize database connection
            self.pool = await asyncpg.create_pool(self.connection_string)
            
            # Check if Apache AGE is installed
            async with self.pool.acquire() as conn:
                # Check for AGE extension
                has_age = await conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'age'
                    )
                """)
                
                if not has_age:
                    self.logger.warning("Apache AGE extension is not installed")
                    # Try to create extension
                    try:
                        await conn.execute("CREATE EXTENSION IF NOT EXISTS age")
                        self.logger.info("Apache AGE extension created")
                    except Exception as e:
                        self.logger.error(f"Failed to create Apache AGE extension: {e}")
                else:
                    self.logger.info("Apache AGE extension is installed")
                
                # Check if graph exists
                try:
                    await conn.execute(f"""
                        LOAD '{self.config.age_schema}';
                        SELECT * FROM ag_catalog.create_graph('{self.config.graph_name}');
                    """)
                    self.logger.info(f"Graph {self.config.graph_name} created or already exists")
                except Exception as e:
                    self.logger.warning(f"Failed to create graph: {e}")
            
            # Initialize NLP components based on configuration
            self._initialize_nlp_components()
            
            # Initialize patterns
            self._initialize_patterns()
        
        except Exception as e:
            self.logger.error(f"Failed to initialize knowledge constructor: {e}")
            raise
        
        self.initialized = True
    
    async def close(self) -> None:
        """Close the knowledge constructor and release resources."""
        if self.pool:
            await self.pool.close()
            self.pool = None
        
        self.initialized = False
    
    def _initialize_nlp_components(self) -> None:
        """Initialize NLP components based on configuration."""
        # Initialize SpaCy if available and needed
        if EntityExtractionMethod.SPACY_NER in [self.config.default_pipeline.entity_extraction_method] or \
           RelationshipExtractionMethod.DEPENDENCY_PARSING in [self.config.default_pipeline.relationship_extraction_method]:
            if SPACY_AVAILABLE:
                try:
                    import spacy
                    self.logger.info(f"Loading SpaCy model: {self.config.spacy_model}")
                    self.spacy_nlp = spacy.load(self.config.spacy_model)
                    self.logger.info("SpaCy model loaded successfully")
                except Exception as e:
                    self.logger.error(f"Failed to load SpaCy model: {e}")
            else:
                self.logger.warning("SpaCy is not available. Some extraction methods will not work.")
        
        # Initialize Transformers if available and needed
        if EntityExtractionMethod.TRANSFORMER_NER in [self.config.default_pipeline.entity_extraction_method] or \
           RelationshipExtractionMethod.TRANSFORMER_RE in [self.config.default_pipeline.relationship_extraction_method]:
            if TRANSFORMERS_AVAILABLE:
                try:
                    from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
                    
                    # Initialize NER pipeline
                    self.logger.info(f"Loading Transformer NER model: {self.config.transformer_model}")
                    self.transformer_ner = pipeline(
                        "ner", 
                        model=self.config.transformer_model, 
                        tokenizer=self.config.transformer_model
                    )
                    self.logger.info("Transformer NER model loaded successfully")
                    
                    # Note: Transformer-based relationship extraction might require a different model
                    # This is a simplified version, in practice you would use a specialized RE model
                except Exception as e:
                    self.logger.error(f"Failed to load Transformer model: {e}")
            else:
                self.logger.warning("Transformers are not available. Some extraction methods will not work.")
    
    def _initialize_patterns(self) -> None:
        """Initialize patterns for rule-based extraction."""
        # Initialize entity patterns
        self.entity_patterns = {
            "PERSON": [
                r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Simple name pattern
                r"\bDr\.\s+[A-Z][a-z]+\b",  # Dr. Name
                r"\bProf\.\s+[A-Z][a-z]+\b",  # Prof. Name
            ],
            "ORGANIZATION": [
                r"\b[A-Z][a-zA-Z]* (Inc|Corp|Corporation|Company|Ltd|LLC)\b",
                r"\b[A-Z][A-Za-z]+ (University|Institute|College)\b",
            ],
            "LOCATION": [
                r"\b[A-Z][a-z]+ (City|Town|Village|County|State|Country)\b",
            ],
            "DATE": [
                r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",  # MM/DD/YYYY
                r"\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b",
            ],
        }
        
        # Add custom entity patterns from config
        for entity_type, patterns in self.config.custom_entity_patterns.items():
            if entity_type in self.entity_patterns:
                self.entity_patterns[entity_type].extend(patterns)
            else:
                self.entity_patterns[entity_type] = patterns
        
        # Initialize relationship patterns
        self.relationship_patterns = {
            "WORKS_FOR": [
                r"(\b[A-Z][a-z]+ [A-Z][a-z]+\b) works for (\b[A-Z][a-zA-Z]* (Inc|Corp|Corporation|Company|Ltd|LLC)\b)",
                r"(\b[A-Z][a-z]+ [A-Z][a-z]+\b) is employed by (\b[A-Z][a-zA-Z]* (Inc|Corp|Corporation|Company|Ltd|LLC)\b)",
            ],
            "LOCATED_IN": [
                r"(\b[A-Z][a-zA-Z]* (Inc|Corp|Corporation|Company|Ltd|LLC)\b) is located in (\b[A-Z][a-z]+ (City|Town|Village|County|State|Country)\b)",
                r"(\b[A-Z][a-z]+ (City|Town|Village|County)\b) is in (\b[A-Z][a-z]+ (State|Country)\b)",
            ],
            "STUDIED_AT": [
                r"(\b[A-Z][a-z]+ [A-Z][a-z]+\b) studied at (\b[A-Z][A-Za-z]+ (University|Institute|College)\b)",
                r"(\b[A-Z][a-z]+ [A-Z][a-z]+\b) graduated from (\b[A-Z][A-Za-z]+ (University|Institute|College)\b)",
            ],
        }
        
        # Add custom relationship patterns from config
        for rel_type, patterns in self.config.custom_relationship_patterns.items():
            if rel_type in self.relationship_patterns:
                self.relationship_patterns[rel_type].extend(patterns)
            else:
                self.relationship_patterns[rel_type] = patterns
    
    async def construct_knowledge_graph(
        self,
        text_sources: List[TextSource],
        pipeline: Optional[ConstructionPipeline] = None
    ) -> ConstructionResult:
        """
        Construct a knowledge graph from text sources.
        
        Args:
            text_sources: List of text sources
            pipeline: Optional custom pipeline configuration
            
        Returns:
            Result of knowledge graph construction
        """
        if not self.initialized:
            await self.initialize()
        
        # Use default pipeline if not provided
        pipeline = pipeline or self.config.default_pipeline
        
        try:
            # Extract knowledge from text sources
            extraction_results = []
            for source in text_sources:
                result = await self.extract_knowledge(source, pipeline)
                extraction_results.append(result)
            
            # Combine extraction results
            all_entities = []
            all_relationships = []
            all_source_ids = []
            
            for result in extraction_results:
                all_entities.extend(result.entities)
                all_relationships.extend(result.relationships)
                all_source_ids.append(result.source_id)
            
            # Deduplicate entities if enabled
            if self.config.deduplication_enabled:
                all_entities = self._deduplicate_entities(all_entities, pipeline.similarity_threshold)
            
            # Validate knowledge if enabled
            if self.config.validation_enabled:
                all_entities, all_relationships = self._validate_knowledge(
                    all_entities, all_relationships, pipeline
                )
            
            # Construct knowledge graph
            construction_id = f"construction_{len(all_source_ids)}_sources_{len(all_entities)}_entities"
            
            # Update graph database
            entity_count, relationship_count = await self._update_graph_database(
                all_entities, all_relationships
            )
            
            # Create construction result
            result = ConstructionResult(
                construction_id=construction_id,
                source_ids=all_source_ids,
                entity_count=entity_count,
                relationship_count=relationship_count,
                success=True,
                metadata={
                    "entity_types": list(set(entity.type for entity in all_entities)),
                    "relationship_types": list(set(rel.type for rel in all_relationships)),
                    "pipeline": pipeline.dict()
                }
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to construct knowledge graph: {e}")
            return ConstructionResult(
                construction_id=f"failed_{len(text_sources)}_sources",
                source_ids=[source.id for source in text_sources],
                success=False,
                error_message=str(e)
            )
    
    async def extract_knowledge(
        self,
        text_source: TextSource,
        pipeline: Optional[ConstructionPipeline] = None
    ) -> ExtractionResult:
        """
        Extract knowledge from a text source.
        
        Args:
            text_source: Text source
            pipeline: Optional custom pipeline configuration
            
        Returns:
            Result of knowledge extraction
        """
        if not self.initialized:
            await self.initialize()
        
        # Use default pipeline if not provided
        pipeline = pipeline or self.config.default_pipeline
        
        # Check cache first
        cache_key = f"extraction_{text_source.id}"
        if self.config.cache_results and cache_key in self.extraction_cache:
            cache_time = self.cache_timestamps.get(cache_key, 0)
            if (asyncio.get_event_loop().time() - cache_time) < self.config.cache_ttl:
                return self.extraction_cache[cache_key]
        
        try:
            # Extract entities
            entities = await self._extract_entities(text_source, pipeline)
            
            # Extract relationships
            relationships = await self._extract_relationships(text_source, entities, pipeline)
            
            # Create triples
            triples = self._create_triples(entities, relationships)
            
            # Create extraction result
            result = ExtractionResult(
                source_id=text_source.id,
                entities=entities,
                relationships=relationships,
                triples=triples,
                metadata={
                    "entity_count": len(entities),
                    "relationship_count": len(relationships),
                    "triple_count": len(triples),
                    "source_type": text_source.source_type,
                    "pipeline": {
                        "entity_method": pipeline.entity_extraction_method,
                        "relationship_method": pipeline.relationship_extraction_method,
                    }
                }
            )
            
            # Cache result
            if self.config.cache_results:
                self.extraction_cache[cache_key] = result
                self.cache_timestamps[cache_key] = asyncio.get_event_loop().time()
            
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to extract knowledge from text source {text_source.id}: {e}")
            return ExtractionResult(
                source_id=text_source.id,
                metadata={"error": str(e)}
            )
    
    async def _extract_entities(
        self,
        text_source: TextSource,
        pipeline: ConstructionPipeline
    ) -> List[Entity]:
        """
        Extract entities from text.
        
        Args:
            text_source: Text source
            pipeline: Pipeline configuration
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Select extraction method
        if pipeline.entity_extraction_method == EntityExtractionMethod.RULE_BASED:
            entities = self._extract_entities_rule_based(text_source)
        
        elif pipeline.entity_extraction_method == EntityExtractionMethod.SPACY_NER:
            if self.spacy_nlp:
                entities = self._extract_entities_spacy(text_source)
            else:
                self.logger.warning("SpaCy NLP not available, falling back to rule-based extraction")
                entities = self._extract_entities_rule_based(text_source)
        
        elif pipeline.entity_extraction_method == EntityExtractionMethod.TRANSFORMER_NER:
            if self.transformer_ner:
                entities = self._extract_entities_transformer(text_source)
            else:
                self.logger.warning("Transformer NER not available, falling back to rule-based extraction")
                entities = self._extract_entities_rule_based(text_source)
        
        # Filter by confidence threshold
        entities = [e for e in entities if e.confidence >= pipeline.entity_confidence_threshold]
        
        # Filter by entity types if specified
        if pipeline.entity_types:
            entities = [e for e in entities if e.type in pipeline.entity_types]
        
        return entities
    
    def _extract_entities_rule_based(self, text_source: TextSource) -> List[Entity]:
        """Extract entities using rule-based patterns."""
        entities = []
        entity_id_counter = 1
        
        # Process each entity type and its patterns
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_source.content)
                for match in matches:
                    entity_id = f"{text_source.id}_entity_{entity_id_counter}"
                    entity_id_counter += 1
                    
                    entity = Entity(
                        id=entity_id,
                        text=match.group(0),
                        type=entity_type,
                        start_char=match.start(),
                        end_char=match.end(),
                        confidence=1.0,  # Rule-based has fixed confidence
                        source_id=text_source.id
                    )
                    
                    entities.append(entity)
        
        return entities
    
    def _extract_entities_spacy(self, text_source: TextSource) -> List[Entity]:
        """Extract entities using SpaCy NER."""
        entities = []
        entity_id_counter = 1
        
        # Process text with SpaCy
        doc = self.spacy_nlp(text_source.content)
        
        # Extract entities
        for ent in doc.ents:
            entity_id = f"{text_source.id}_entity_{entity_id_counter}"
            entity_id_counter += 1
            
            entity = Entity(
                id=entity_id,
                text=ent.text,
                type=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char,
                confidence=0.8,  # SpaCy doesn't provide confidence, using a default
                source_id=text_source.id
            )
            
            entities.append(entity)
        
        return entities
    
    def _extract_entities_transformer(self, text_source: TextSource) -> List[Entity]:
        """Extract entities using Transformer-based NER."""
        entities = []
        entity_id_counter = 1
        
        # Process text with transformer NER
        # This implementation assumes the text fits within the model's max token length
        # In practice, you should chunk the text if it's too long
        try:
            # Run NER
            ner_results = self.transformer_ner(text_source.content)
            
            # Group by entity (transformer tokenization can split entities)
            current_entity = None
            
            for token in ner_results:
                # New entity or continuation
                token_label = token["entity"]
                
                # Skip 'O' (outside) labels
                if token_label == "O":
                    current_entity = None
                    continue
                
                # Extract entity type from BIO format (B-PER, I-PER, etc.)
                if "-" in token_label:
                    prefix, entity_type = token_label.split("-", 1)
                else:
                    entity_type = token_label
                
                # Start of a new entity
                if current_entity is None or token_label.startswith("B-"):
                    entity_id = f"{text_source.id}_entity_{entity_id_counter}"
                    entity_id_counter += 1
                    
                    current_entity = {
                        "id": entity_id,
                        "text": token["word"],
                        "type": entity_type,
                        "start_char": token["start"],
                        "end_char": token["end"],
                        "confidence": token["score"],
                        "source_id": text_source.id
                    }
                    
                    entities.append(Entity(**current_entity))
                
                # Continuation of an entity
                elif token_label.startswith("I-"):
                    # Update the end position
                    entity = entities[-1]
                    entity.text += " " + token["word"].lstrip("##")  # Handle BERT tokenization
                    entity.end_char = token["end"]
                    entity.confidence = (entity.confidence + token["score"]) / 2  # Average confidence
        
        except Exception as e:
            self.logger.error(f"Error in transformer NER extraction: {e}")
        
        return entities
    
    async def _extract_relationships(
        self,
        text_source: TextSource,
        entities: List[Entity],
        pipeline: ConstructionPipeline
    ) -> List[Relationship]:
        """
        Extract relationships between entities.
        
        Args:
            text_source: Text source
            entities: List of entities
            pipeline: Pipeline configuration
            
        Returns:
            List of extracted relationships
        """
        relationships = []
        
        # Select extraction method
        if pipeline.relationship_extraction_method == RelationshipExtractionMethod.PATTERN_BASED:
            relationships = self._extract_relationships_pattern_based(text_source, entities)
        
        elif pipeline.relationship_extraction_method == RelationshipExtractionMethod.DEPENDENCY_PARSING:
            if self.spacy_nlp:
                relationships = self._extract_relationships_dependency_parsing(text_source, entities)
            else:
                self.logger.warning("SpaCy NLP not available, falling back to pattern-based extraction")
                relationships = self._extract_relationships_pattern_based(text_source, entities)
        
        elif pipeline.relationship_extraction_method == RelationshipExtractionMethod.TRANSFORMER_RE:
            if self.transformer_re:
                relationships = self._extract_relationships_transformer(text_source, entities)
            else:
                self.logger.warning("Transformer RE not available, falling back to pattern-based extraction")
                relationships = self._extract_relationships_pattern_based(text_source, entities)
        
        # Filter by confidence threshold
        relationships = [r for r in relationships if r.confidence >= pipeline.relationship_confidence_threshold]
        
        # Filter by relationship types if specified
        if pipeline.relationship_types:
            relationships = [r for r in relationships if r.type in pipeline.relationship_types]
        
        return relationships
    
    def _extract_relationships_pattern_based(
        self,
        text_source: TextSource,
        entities: List[Entity]
    ) -> List[Relationship]:
        """Extract relationships using pattern matching."""
        relationships = []
        relationship_id_counter = 1
        
        # Create entity dictionary for quick lookup
        entity_dict = {entity.id: entity for entity in entities}
        
        # Process each relationship type and its patterns
        for relationship_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_source.content)
                for match in matches:
                    # The pattern should have two capture groups
                    if len(match.groups()) >= 2:
                        subject_text = match.group(1)
                        object_text = match.group(2)
                        
                        # Find entities that match the subject and object
                        subject_entity = None
                        object_entity = None
                        
                        for entity in entities:
                            if entity.text == subject_text:
                                subject_entity = entity
                            elif entity.text == object_text:
                                object_entity = entity
                        
                        # Create relationship if both entities were found
                        if subject_entity and object_entity:
                            relationship_id = f"{text_source.id}_relationship_{relationship_id_counter}"
                            relationship_id_counter += 1
                            
                            relationship = Relationship(
                                id=relationship_id,
                                source_entity_id=subject_entity.id,
                                target_entity_id=object_entity.id,
                                type=relationship_type,
                                text=match.group(0),
                                confidence=1.0,  # Pattern-based has fixed confidence
                                source_id=text_source.id
                            )
                            
                            relationships.append(relationship)
        
        return relationships
    
    def _extract_relationships_dependency_parsing(
        self,
        text_source: TextSource,
        entities: List[Entity]
    ) -> List[Relationship]:
        """Extract relationships using dependency parsing."""
        relationships = []
        relationship_id_counter = 1
        
        # Process text with SpaCy
        doc = self.spacy_nlp(text_source.content)
        
        # Create a map of character spans to entities
        span_to_entity = {}
        for entity in entities:
            span_to_entity[(entity.start_char, entity.end_char)] = entity
        
        # Find potential subject-verb-object triples
        for sent in doc.sents:
            # Find the root verb
            root = None
            for token in sent:
                if token.dep_ == "ROOT" and token.pos_ == "VERB":
                    root = token
                    break
            
            if not root:
                continue
            
            # Find subjects and objects
            subjects = []
            objects = []
            
            for token in sent:
                if token.dep_ in ("nsubj", "nsubjpass") and token.head == root:
                    # If the subject token is part of a named entity, use that
                    if token.ent_type_:
                        for ent in doc.ents:
                            if token in ent:
                                # Check if this entity is in our extracted entities
                                for entity in entities:
                                    if entity.start_char <= ent.start_char and entity.end_char >= ent.end_char:
                                        subjects.append(entity)
                                        break
                                break
                
                elif token.dep_ in ("dobj", "pobj") and (token.head == root or token.head.head == root):
                    # If the object token is part of a named entity, use that
                    if token.ent_type_:
                        for ent in doc.ents:
                            if token in ent:
                                # Check if this entity is in our extracted entities
                                for entity in entities:
                                    if entity.start_char <= ent.start_char and entity.end_char >= ent.end_char:
                                        objects.append(entity)
                                        break
                                break
            
            # Create relationships from subject-verb-object triples
            for subject in subjects:
                for obj in objects:
                    relationship_id = f"{text_source.id}_relationship_{relationship_id_counter}"
                    relationship_id_counter += 1
                    
                    relationship = Relationship(
                        id=relationship_id,
                        source_entity_id=subject.id,
                        target_entity_id=obj.id,
                        type=root.lemma_.upper(),
                        text=f"{subject.text} {root.text} {obj.text}",
                        confidence=0.7,  # Dependency parsing confidence
                        source_id=text_source.id
                    )
                    
                    relationships.append(relationship)
        
        return relationships
    
    def _extract_relationships_transformer(
        self,
        text_source: TextSource,
        entities: List[Entity]
    ) -> List[Relationship]:
        """Extract relationships using transformer-based models."""
        # This is a placeholder for transformer-based relationship extraction
        # In practice, you would use a specialized RE model
        self.logger.warning("Transformer-based relationship extraction not fully implemented")
        return []
    
    def _create_triples(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> List[Triple]:
        """
        Create knowledge triples from entities and relationships.
        
        Args:
            entities: List of entities
            relationships: List of relationships
            
        Returns:
            List of knowledge triples
        """
        triples = []
        
        # Create entity dictionary for quick lookup
        entity_dict = {entity.id: entity for entity in entities}
        
        # Convert relationships to triples
        for relationship in relationships:
            subject = entity_dict.get(relationship.source_entity_id)
            object_entity = entity_dict.get(relationship.target_entity_id)
            
            if subject and object_entity:
                triple = Triple(
                    subject=subject,
                    predicate=relationship.type,
                    object=object_entity,
                    confidence=relationship.confidence,
                    metadata=relationship.metadata,
                    source_id=relationship.source_id
                )
                
                triples.append(triple)
        
        return triples
    
    def _deduplicate_entities(
        self,
        entities: List[Entity],
        similarity_threshold: float
    ) -> List[Entity]:
        """
        Deduplicate entities based on text similarity.
        
        Args:
            entities: List of entities
            similarity_threshold: Threshold for considering entities as duplicates
            
        Returns:
            Deduplicated list of entities
        """
        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            
            entities_by_type[entity.type].append(entity)
        
        # Deduplicate within each type
        deduplicated_entities = []
        entity_mapping = {}  # Maps original entity IDs to deduplicated entity IDs
        
        for entity_type, type_entities in entities_by_type.items():
            # Sort by confidence (descending)
            type_entities.sort(key=lambda e: e.confidence, reverse=True)
            
            # Process each entity
            for entity in type_entities:
                # Check if this entity is similar to any already processed entity
                found_duplicate = False
                
                for processed in deduplicated_entities:
                    if processed.type == entity.type:
                        similarity = self._calculate_text_similarity(entity.text, processed.text)
                        
                        if similarity >= similarity_threshold:
                            # Found a duplicate
                            found_duplicate = True
                            entity_mapping[entity.id] = processed.id
                            break
                
                if not found_duplicate:
                    # No duplicate found, add to deduplicated list
                    deduplicated_entities.append(entity)
                    entity_mapping[entity.id] = entity.id
        
        return deduplicated_entities
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        This is a simple implementation using character-level Jaccard similarity.
        In practice, you might want to use more sophisticated methods.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        # Convert to lowercase for comparison
        text1 = text1.lower()
        text2 = text2.lower()
        
        # Character-level Jaccard similarity
        set1 = set(text1)
        set2 = set(text2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0
        
        return intersection / union
    
    def _validate_knowledge(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        pipeline: ConstructionPipeline
    ) -> Tuple[List[Entity], List[Relationship]]:
        """
        Validate extracted knowledge.
        
        Args:
            entities: List of entities
            relationships: List of relationships
            pipeline: Pipeline configuration
            
        Returns:
            Tuple of validated entities and relationships
        """
        # Already filtered by confidence threshold in extraction methods
        # Additional validation can be implemented here
        
        if pipeline.validation_method == ValidationMethod.CROSS_REFERENCE:
            # This could involve checking against existing knowledge graph
            # or external sources, simplified implementation
            pass
        
        elif pipeline.validation_method == ValidationMethod.HUMAN_IN_LOOP:
            # In a real implementation, this would involve a human review step
            self.logger.warning("Human-in-the-loop validation not implemented")
        
        return entities, relationships
    
    async def _update_graph_database(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> Tuple[int, int]:
        """
        Update the graph database with extracted knowledge.
        
        Args:
            entities: List of entities
            relationships: List of relationships
            
        Returns:
            Tuple of (entity_count, relationship_count) added to the graph
        """
        if not self.pool:
            self.logger.error("Database connection not initialized")
            return 0, 0
        
        entity_count = 0
        relationship_count = 0
        
        try:
            async with self.pool.acquire() as conn:
                # Load AGE extension
                await conn.execute(f"LOAD '{self.config.age_schema}';")
                
                # Set graph
                await conn.execute(f"SET graph_path = {self.config.graph_name};")
                
                # Create entities
                for entity in entities:
                    # Create properties object
                    properties = {
                        "text": entity.text,
                        "type": entity.type,
                        "confidence": entity.confidence,
                        "source_id": entity.source_id or "unknown"
                    }
                    
                    if self.config.create_node_properties:
                        # Add metadata
                        for key, value in entity.metadata.items():
                            properties[key] = value
                    
                    # Convert properties to JSON string
                    properties_json = json.dumps(properties)
                    
                    # Create entity
                    cypher = f"""
                        CREATE (n:{entity.type} {{
                            id: '{entity.id}',
                            properties: {properties_json}::jsonb
                        }})
                        RETURN id(n)
                    """
                    
                    try:
                        node_id = await conn.fetchval(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (id agtype);", 
                                                  cypher, {}, True)
                        
                        if node_id:
                            entity_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to create entity {entity.id}: {e}")
                
                # Create relationships
                for relationship in relationships:
                    # Create properties object
                    properties = {
                        "text": relationship.text,
                        "confidence": relationship.confidence,
                        "source_id": relationship.source_id or "unknown"
                    }
                    
                    if self.config.create_relationship_properties:
                        # Add metadata
                        for key, value in relationship.metadata.items():
                            properties[key] = value
                    
                    # Convert properties to JSON string
                    properties_json = json.dumps(properties)
                    
                    # Create relationship
                    cypher = f"""
                        MATCH (a), (b)
                        WHERE a.id = '{relationship.source_entity_id}' AND b.id = '{relationship.target_entity_id}'
                        CREATE (a)-[r:{relationship.type} {{
                            id: '{relationship.id}',
                            properties: {properties_json}::jsonb
                        }}]->(b)
                        RETURN id(r)
                    """
                    
                    try:
                        rel_id = await conn.fetchval(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (id agtype);", 
                                                 cypher, {}, True)
                        
                        if rel_id:
                            relationship_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to create relationship {relationship.id}: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to update graph database: {e}")
        
        return entity_count, relationship_count
    
    async def query_graph(self, cypher_query: str) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query against the knowledge graph.
        
        Args:
            cypher_query: Cypher query string
            
        Returns:
            Query results
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            async with self.pool.acquire() as conn:
                # Load AGE extension
                await conn.execute(f"LOAD '{self.config.age_schema}';")
                
                # Set graph
                await conn.execute(f"SET graph_path = {self.config.graph_name};")
                
                # Execute query
                result = await conn.fetch(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (result agtype);", 
                                       cypher_query, {}, True)
                
                # Parse results
                parsed_results = []
                for row in result:
                    parsed_results.append(json.loads(row['result']))
                
                return parsed_results
        
        except Exception as e:
            self.logger.error(f"Failed to execute Cypher query: {e}")
            return []
    
    async def export_graph(self, format: str = "json") -> Dict[str, Any]:
        """
        Export the knowledge graph.
        
        Args:
            format: Export format (json, cypher, etc.)
            
        Returns:
            Exported graph data
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Query all nodes
            nodes = await self.query_graph("""
                MATCH (n)
                RETURN n
            """)
            
            # Query all relationships
            relationships = await self.query_graph("""
                MATCH ()-[r]->()
                RETURN r
            """)
            
            # Create export data
            export_data = {
                "graph_name": self.config.graph_name,
                "nodes": nodes,
                "relationships": relationships,
                "metadata": {
                    "node_count": len(nodes),
                    "relationship_count": len(relationships),
                    "exported_at": asyncio.get_event_loop().time()
                }
            }
            
            # Format-specific processing
            if format == "json":
                return export_data
            elif format == "cypher":
                # Generate Cypher script
                cypher_script = "// Knowledge Graph Export\n\n"
                
                # Create nodes
                cypher_script += "// Nodes\n"
                for node in nodes:
                    node_labels = ":".join(node.get("labels", ["Node"]))
                    node_props = json.dumps(node.get("properties", {}))
                    cypher_script += f"CREATE (:{node_labels} {node_props});\n"
                
                # Create relationships
                cypher_script += "\n// Relationships\n"
                for rel in relationships:
                    rel_type = rel.get("type", "RELATED_TO")
                    rel_props = json.dumps(rel.get("properties", {}))
                    cypher_script += f"MATCH (a), (b) WHERE id(a) = {rel.get('start_id')} AND id(b) = {rel.get('end_id')} CREATE (a)-[:{rel_type} {rel_props}]->(b);\n"
                
                return {"cypher": cypher_script}
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        except Exception as e:
            self.logger.error(f"Failed to export graph: {e}")
            return {"error": str(e)}


# Factory function for knowledge constructors
async def create_knowledge_constructor(
    connection_string: str,
    graph_name: str = "knowledge_graph",
    logger: Optional[logging.Logger] = None
) -> KnowledgeConstructor:
    """
    Create a knowledge constructor instance.
    
    Args:
        connection_string: Database connection string
        graph_name: Name of the graph
        logger: Optional logger
        
    Returns:
        Initialized knowledge constructor
    """
    config = KnowledgeConstructorConfig(
        graph_name=graph_name,
        spacy_model="en_core_web_sm",
        transformer_model="dslim/bert-base-NER",
        deduplication_enabled=True,
        validation_enabled=True
    )
    
    constructor = KnowledgeConstructor(connection_string, config, logger=logger)
    await constructor.initialize()
    
    return constructor