"""
Tests for the KnowledgeConstructor class.

This module contains tests for the KnowledgeConstructor class which
provides functionality to extract entities and relationships from text
and build knowledge graphs.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any, Optional

from uno.ai.graph_integration.knowledge_constructor import (
    KnowledgeConstructor,
    KnowledgeConstructorConfig,
    EntityExtractionMethod,
    RelationshipExtractionMethod,
    ValidationMethod,
    TextSource,
    Entity,
    Relationship,
    Triple,
    ConstructionPipeline,
    ExtractionResult,
    ConstructionResult,
    create_knowledge_constructor
)


class TestKnowledgeConstructor:
    """Tests for the KnowledgeConstructor class."""
    
    @pytest.fixture
    def mock_pool(self):
        """Create a mock connection pool."""
        mock = MagicMock()
        mock.acquire = AsyncMock()
        mock.close = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_conn(self):
        """Create a mock database connection."""
        mock = MagicMock()
        mock.execute = AsyncMock()
        mock.fetchval = AsyncMock()
        mock.fetch = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_asyncpg(self):
        """Mock asyncpg module."""
        with patch("uno.ai.graph_integration.knowledge_constructor.asyncpg") as mock:
            mock.create_pool = AsyncMock()
            yield mock
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return KnowledgeConstructorConfig(
            age_schema="ag_catalog",
            graph_name="knowledge_graph",
            default_pipeline=ConstructionPipeline(
                entity_extraction_method=EntityExtractionMethod.RULE_BASED,
                relationship_extraction_method=RelationshipExtractionMethod.PATTERN_BASED,
                validation_method=ValidationMethod.CONFIDENCE_THRESHOLD,
                entity_confidence_threshold=0.5,
                relationship_confidence_threshold=0.7
            ),
            custom_entity_patterns={
                "ORGANIZATION": [r"\b[A-Z][a-zA-Z]+ (Inc|Corp|Company)\b"],
                "LOCATION": [r"\b[A-Z][a-z]+ (City|County|State)\b"]
            },
            custom_relationship_patterns={
                "LOCATED_IN": [r"(\b[A-Z][a-zA-Z]+ (Inc|Corp|Company)\b) (?:is located|is based) in (\b[A-Z][a-z]+ (City|County|State)\b)"]
            },
            deduplication_enabled=True,
            validation_enabled=True,
            cache_results=True,
            cache_ttl=60,
            timeout=30
        )
    
    @pytest.fixture
    async def constructor(self, mock_asyncpg, mock_pool, mock_conn, config):
        """Create a test knowledge constructor with mocked dependencies."""
        mock_asyncpg.create_pool.return_value = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchval.return_value = True
        
        constructor = KnowledgeConstructor(
            connection_string="postgresql://test:test@localhost:5432/testdb",
            config=config
        )
        await constructor.initialize()
        return constructor
    
    @pytest.mark.asyncio
    async def test_initialize(self, constructor, mock_asyncpg, mock_conn):
        """Test initialization of the knowledge constructor."""
        # Check that the pool was created
        mock_asyncpg.create_pool.assert_called_once_with(
            "postgresql://test:test@localhost:5432/testdb"
        )
        
        # Check that AGE extension was checked
        mock_conn.fetchval.assert_called_once()
        assert "extname = 'age'" in mock_conn.fetchval.call_args[0][0]
        
        # Check that initialization is complete
        assert constructor.initialized is True
        
        # Check that patterns were initialized
        assert "ORGANIZATION" in constructor.entity_patterns
        assert "LOCATION" in constructor.entity_patterns
        assert "LOCATED_IN" in constructor.relationship_patterns
    
    @pytest.mark.asyncio
    async def test_close(self, constructor, mock_pool):
        """Test closing the constructor."""
        await constructor.close()
        
        # Check that the pool was closed
        mock_pool.close.assert_called_once()
        
        # Check that initialized is set to False
        assert constructor.initialized is False
    
    @pytest.mark.asyncio
    async def test_extract_knowledge_rule_based(self, constructor):
        """Test extracting knowledge using rule-based methods."""
        # Create a text source
        source = TextSource(
            id="source1",
            content="Acme Corp is based in New York City. John Smith is the CEO of Acme Corp."
        )
        
        # Use rule-based extraction
        pipeline = ConstructionPipeline(
            entity_extraction_method=EntityExtractionMethod.RULE_BASED,
            relationship_extraction_method=RelationshipExtractionMethod.PATTERN_BASED
        )
        
        # Extract knowledge
        result = await constructor.extract_knowledge(source, pipeline)
        
        # Check the result
        assert isinstance(result, ExtractionResult)
        assert result.source_id == "source1"
        
        # Should find at least some entities
        assert len(result.entities) > 0
        
        # Check for specific entities
        acme_found = False
        nyc_found = False
        for entity in result.entities:
            if "Acme Corp" in entity.text:
                acme_found = True
            if "New York City" in entity.text:
                nyc_found = True
        
        # At least one of the entities should be found
        assert acme_found or nyc_found
    
    @pytest.mark.asyncio
    async def test_extract_relationships_pattern_based(self, constructor):
        """Test extracting relationships using pattern-based methods."""
        # Create a text source with a clear relationship
        source = TextSource(
            id="source1",
            content="Acme Corp is located in New York City."
        )
        
        # Create entities manually (since we're testing relationship extraction)
        entities = [
            Entity(
                id="entity1",
                text="Acme Corp",
                type="ORGANIZATION",
                start_char=0,
                end_char=9,
                confidence=1.0,
                source_id="source1"
            ),
            Entity(
                id="entity2",
                text="New York City",
                type="LOCATION",
                start_char=23,
                end_char=36,
                confidence=1.0,
                source_id="source1"
            )
        ]
        
        # Extract relationships
        relationships = await constructor._extract_relationships_pattern_based(source, entities)
        
        # Should find the "LOCATED_IN" relationship
        assert len(relationships) > 0
        
        # Check the relationship details
        found_located_in = False
        for relationship in relationships:
            if relationship.type == "LOCATED_IN":
                found_located_in = True
                assert relationship.source_entity_id == "entity1"
                assert relationship.target_entity_id == "entity2"
        
        assert found_located_in
    
    @pytest.mark.asyncio
    async def test_create_triples(self, constructor):
        """Test creating knowledge triples from entities and relationships."""
        # Create entities
        entities = [
            Entity(
                id="entity1",
                text="Acme Corp",
                type="ORGANIZATION",
                start_char=0,
                end_char=9,
                confidence=1.0,
                source_id="source1"
            ),
            Entity(
                id="entity2",
                text="New York City",
                type="LOCATION",
                start_char=23,
                end_char=36,
                confidence=1.0,
                source_id="source1"
            )
        ]
        
        # Create a relationship
        relationships = [
            Relationship(
                id="rel1",
                source_entity_id="entity1",
                target_entity_id="entity2",
                type="LOCATED_IN",
                text="Acme Corp is located in New York City",
                confidence=1.0,
                source_id="source1"
            )
        ]
        
        # Create triples
        triples = constructor._create_triples(entities, relationships)
        
        # Check the triples
        assert len(triples) == 1
        assert triples[0].subject.id == "entity1"
        assert triples[0].predicate == "LOCATED_IN"
        assert triples[0].object.id == "entity2"
        assert triples[0].confidence == 1.0
    
    @pytest.mark.asyncio
    async def test_deduplicate_entities(self, constructor):
        """Test deduplicating entities based on text similarity."""
        # Create duplicate entities
        entities = [
            Entity(
                id="entity1",
                text="Acme Corporation",
                type="ORGANIZATION",
                start_char=0,
                end_char=16,
                confidence=0.8,
                source_id="source1"
            ),
            Entity(
                id="entity2",
                text="Acme Corp",
                type="ORGANIZATION",
                start_char=50,
                end_char=59,
                confidence=0.9,
                source_id="source1"
            ),
            Entity(
                id="entity3",
                text="New York City",
                type="LOCATION",
                start_char=23,
                end_char=36,
                confidence=1.0,
                source_id="source1"
            )
        ]
        
        # Deduplicate entities
        deduplicated = constructor._deduplicate_entities(entities, similarity_threshold=0.7)
        
        # Should reduce to 2 entities (keeping the higher confidence one for Acme)
        assert len(deduplicated) == 2
        
        # Check that the higher confidence "Acme" entity was kept
        acme_entity = next((e for e in deduplicated if "Acme" in e.text), None)
        assert acme_entity is not None
        assert acme_entity.id == "entity2"  # The higher confidence one
        
        # The other entity should still be there
        assert any(e.id == "entity3" for e in deduplicated)
    
    @pytest.mark.asyncio
    async def test_calculate_text_similarity(self, constructor):
        """Test calculating text similarity."""
        # Test exact match
        similarity = constructor._calculate_text_similarity("apple", "apple")
        assert similarity == 1.0
        
        # Test similar words
        similarity = constructor._calculate_text_similarity("apple", "apples")
        assert similarity > 0.8
        
        # Test different words
        similarity = constructor._calculate_text_similarity("apple", "banana")
        assert similarity < 0.5
        
        # Test case insensitivity
        similarity = constructor._calculate_text_similarity("Apple", "apple")
        assert similarity == 1.0
    
    @pytest.mark.asyncio
    async def test_update_graph_database(self, constructor, mock_conn):
        """Test updating the graph database with extracted knowledge."""
        # Create entities
        entities = [
            Entity(
                id="entity1",
                text="Acme Corp",
                type="ORGANIZATION",
                start_char=0,
                end_char=9,
                confidence=1.0,
                source_id="source1"
            ),
            Entity(
                id="entity2",
                text="New York City",
                type="LOCATION",
                start_char=23,
                end_char=36,
                confidence=1.0,
                source_id="source1"
            )
        ]
        
        # Create a relationship
        relationships = [
            Relationship(
                id="rel1",
                source_entity_id="entity1",
                target_entity_id="entity2",
                type="LOCATED_IN",
                text="Acme Corp is located in New York City",
                confidence=1.0,
                source_id="source1"
            )
        ]
        
        # Mock fetch responses for node and relationship creation
        mock_conn.fetchval.side_effect = ["node1", "node2", "rel1"]
        
        # Update graph database
        entity_count, relationship_count = await constructor._update_graph_database(entities, relationships)
        
        # Check counts
        assert entity_count == 2
        assert relationship_count == 1
        
        # Check that the correct queries were executed
        assert mock_conn.fetchval.call_count == 3
        
        # Check entity creation queries
        for i, call in enumerate(mock_conn.fetchval.call_args_list[:2]):
            query = call[0][1]
            assert "CREATE (n:" in query
            assert "properties:" in query
            
            # First call should create ORGANIZATION node, second should create LOCATION node
            if i == 0:
                assert "ORGANIZATION" in query
                assert "Acme Corp" in query
            else:
                assert "LOCATION" in query
                assert "New York City" in query
        
        # Check relationship creation query
        rel_query = mock_conn.fetchval.call_args_list[2][0][1]
        assert "MATCH (a), (b)" in rel_query
        assert "CREATE (a)-[r:LOCATED_IN" in rel_query
    
    @pytest.mark.asyncio
    async def test_construct_knowledge_graph(self, constructor, mock_conn):
        """Test constructing a knowledge graph from text sources."""
        # Create text sources
        sources = [
            TextSource(
                id="source1",
                content="Acme Corp is located in New York City. John Smith is the CEO of Acme Corp."
            ),
            TextSource(
                id="source2",
                content="Acme Corp was founded in 1990 by John Smith."
            )
        ]
        
        # Mock entity and relationship creation responses
        mock_conn.fetchval.side_effect = ["node1", "node2", "node3", "rel1", "rel2"]
        
        # Construct knowledge graph
        result = await constructor.construct_knowledge_graph(sources)
        
        # Check result
        assert isinstance(result, ConstructionResult)
        assert result.success is True
        assert len(result.source_ids) == 2
        assert "source1" in result.source_ids
        assert "source2" in result.source_ids
        
        # Should have created some entities and relationships
        assert result.entity_count > 0
        assert result.relationship_count > 0
    
    @pytest.mark.asyncio
    async def test_query_graph(self, constructor, mock_conn):
        """Test querying the knowledge graph."""
        # Create a cypher query
        cypher = """
        MATCH (org:ORGANIZATION)-[r:LOCATED_IN]->(loc:LOCATION)
        WHERE org.properties->>'text' = 'Acme Corp'
        RETURN org, loc
        """
        
        # Mock query results
        mock_conn.fetch.return_value = [
            MagicMock(result=json.dumps({
                "id": "node1",
                "labels": ["ORGANIZATION"],
                "properties": {"text": "Acme Corp"}
            })),
            MagicMock(result=json.dumps({
                "id": "node2",
                "labels": ["LOCATION"],
                "properties": {"text": "New York City"}
            }))
        ]
        
        # Query the graph
        results = await constructor.query_graph(cypher)
        
        # Check results
        assert len(results) == 2
        assert results[0]["id"] == "node1"
        assert results[1]["id"] == "node2"
        
        # Check that the correct query was executed
        query = mock_conn.fetch.call_args[0][0]
        assert "cypher('knowledge_graph'" in query
        assert f"${cypher}" in query
    
    @pytest.mark.asyncio
    async def test_export_graph(self, constructor, mock_conn):
        """Test exporting the knowledge graph."""
        # Mock query results for nodes and relationships
        mock_conn.fetch.side_effect = [
            [
                MagicMock(result=json.dumps({
                    "id": "node1",
                    "labels": ["ORGANIZATION"],
                    "properties": {"text": "Acme Corp"}
                })),
                MagicMock(result=json.dumps({
                    "id": "node2",
                    "labels": ["LOCATION"],
                    "properties": {"text": "New York City"}
                }))
            ],
            [
                MagicMock(result=json.dumps({
                    "id": "rel1",
                    "type": "LOCATED_IN",
                    "start_id": "node1",
                    "end_id": "node2",
                    "properties": {"text": "Acme Corp is located in New York City"}
                }))
            ]
        ]
        
        # Export the graph
        export_data = await constructor.export_graph(format="json")
        
        # Check export data
        assert export_data["graph_name"] == "knowledge_graph"
        assert len(export_data["nodes"]) == 2
        assert len(export_data["relationships"]) == 1
        assert export_data["metadata"]["node_count"] == 2
        assert export_data["metadata"]["relationship_count"] == 1
        
        # Export as Cypher
        cypher_export = await constructor.export_graph(format="cypher")
        
        # Check Cypher export
        assert "cypher" in cypher_export
        assert "// Nodes" in cypher_export["cypher"]
        assert "// Relationships" in cypher_export["cypher"]
        assert "CREATE (:ORGANIZATION" in cypher_export["cypher"]
        assert "CREATE (a)-[:LOCATED_IN" in cypher_export["cypher"]
    
    @pytest.mark.asyncio
    async def test_create_knowledge_constructor(self, mock_asyncpg, mock_pool, mock_conn):
        """Test the factory function to create a knowledge constructor."""
        # Mock the database connection
        mock_asyncpg.create_pool.return_value = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchval.return_value = True
        
        # Call the factory function
        constructor = await create_knowledge_constructor(
            connection_string="postgresql://test:test@localhost:5432/testdb",
            graph_name="test_knowledge_graph"
        )
        
        # Check the constructor
        assert constructor is not None
        assert constructor.initialized is True
        assert constructor.config.graph_name == "test_knowledge_graph"
        assert constructor.connection_string == "postgresql://test:test@localhost:5432/testdb"