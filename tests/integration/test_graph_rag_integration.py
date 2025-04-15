"""
Integration tests for Graph-Enhanced RAG functionality.

This module contains integration tests that verify the proper functioning of
GraphRAGService with actual database connections and Apache AGE.
"""

import pytest
import asyncio
import json
from typing import Dict, List, Any, Optional

from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, MetaData
from sqlalchemy.orm import relationship, declarative_base

from uno.domain.core import Entity
from uno.domain.vector_search import VectorSearchService, VectorQuery, RAGService
from uno.ai.graph_integration.graph_navigator import create_graph_navigator
from uno.ai.graph_integration.knowledge_constructor import (
    create_knowledge_constructor,
    TextSource
)
from uno.ai.graph_integration.graph_rag import GraphRAGService, create_graph_rag_service
from uno.sql.emitters.graph import GraphSQLEmitter
from uno.sql.emitters.vector import VectorSearchEmitter


Base = declarative_base()


class Document(Base):
    """Test document entity for testing RAG."""
    
    __tablename__ = "test_rag_documents"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("test_rag_categories.id"))
    
    # Relationship
    category = relationship("Category", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}')>"


class Category(Base):
    """Test category for document classification."""
    
    __tablename__ = "test_rag_categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    
    # Relationship
    documents = relationship("Document", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class TestEntity(Entity):
    """Entity wrapper for Document."""
    id: str
    title: str
    content: str
    category_id: str


class TestGraphRAGIntegration:
    """Integration tests for Graph-Enhanced RAG."""
    
    @pytest.fixture(scope="module")
    async def db_setup(self, connection_pool):
        """Set up test database for RAG integration tests."""
        async with connection_pool.connect() as conn:
            # Create test tables
            await conn.execute(text("""
                DROP TABLE IF EXISTS test_rag_documents CASCADE;
                DROP TABLE IF EXISTS test_rag_categories CASCADE;
                DROP TABLE IF EXISTS test_rag_embeddings CASCADE;
                
                CREATE TABLE test_rag_categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT
                );
                
                CREATE TABLE test_rag_documents (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    category_id INTEGER REFERENCES test_rag_categories(id)
                );
                
                -- Create embeddings table
                CREATE TABLE test_rag_embeddings (
                    id INTEGER PRIMARY KEY REFERENCES test_rag_documents(id),
                    embedding vector(384) NOT NULL,
                    text_content TEXT NOT NULL
                );
                
                -- Create index on embedding
                CREATE INDEX test_rag_embeddings_vector_idx 
                ON test_rag_embeddings USING ivfflat (embedding vector_cosine_ops);
                
                -- Insert test categories
                INSERT INTO test_rag_categories (id, name, description) VALUES 
                (1, 'Technology', 'Articles about technology and computing'),
                (2, 'Science', 'Scientific articles and research'),
                (3, 'Health', 'Health and medical information');
                
                -- Insert test documents
                INSERT INTO test_rag_documents (id, title, content, category_id) VALUES 
                (1, 'Introduction to Python', 'Python is a programming language that lets you work quickly and integrate systems more effectively.', 1),
                (2, 'Machine Learning Basics', 'Machine learning is a branch of artificial intelligence focused on building systems that learn from data.', 1),
                (3, 'Climate Change Research', 'Recent studies show accelerating warming trends across the globe with significant environmental impacts.', 2),
                (4, 'Healthy Diet Tips', 'A balanced diet includes a variety of foods that provide essential nutrients for good health.', 3),
                (5, 'Solar System Exploration', 'Astronomers continue to discover new objects in our solar system beyond the traditional nine planets.', 2);
                
                -- Insert test embeddings (simplified fixed vectors for testing)
                INSERT INTO test_rag_embeddings (id, embedding, text_content) VALUES 
                (1, '[0.1, 0.2, 0.3]'::vector, 'Python programming language'),
                (2, '[0.2, 0.3, 0.4]'::vector, 'Machine learning artificial intelligence'),
                (3, '[0.3, 0.4, 0.5]'::vector, 'Climate change environment research'),
                (4, '[0.4, 0.5, 0.6]'::vector, 'Healthy diet nutrition'),
                (5, '[0.5, 0.6, 0.7]'::vector, 'Solar system astronomy planets');
            """))
            
            # Load AGE extension
            await conn.execute(text("LOAD 'age';"))
            
            # Create or reset graph
            await conn.execute(text("""
                SELECT * FROM ag_catalog.drop_graph('test_rag_graph', true);
                SELECT * FROM ag_catalog.create_graph('test_rag_graph');
            """))
            
            # Create graph function for testing
            await conn.execute(text("""
                -- Create helper function for graph traversal if it doesn't exist
                CREATE OR REPLACE FUNCTION graph_traverse(
                    start_label TEXT, 
                    start_filters JSONB, 
                    path_pattern TEXT
                ) RETURNS TABLE (id TEXT, distance INTEGER) AS $$
                DECLARE
                    cypher_query TEXT;
                BEGIN
                    cypher_query := 'MATCH path = (start:' || start_label || ')-' || path_pattern || 
                                  'WHERE ';
                    
                    -- Add filters for the start node
                    FOR key_value IN SELECT * FROM jsonb_each(start_filters)
                    LOOP
                        cypher_query := cypher_query || 'start.' || key_value.key || 
                                      ' = ''' || key_value.value::TEXT || ''' AND ';
                    END LOOP;
                    
                    -- Remove trailing 'AND' if filters were added
                    IF start_filters != '{}'::JSONB THEN
                        cypher_query := substring(cypher_query, 1, length(cypher_query) - 5);
                    ELSE
                        -- Remove 'WHERE' if no filters
                        cypher_query := substring(cypher_query, 1, length(cypher_query) - 6);
                    END IF;
                    
                    cypher_query := cypher_query || 
                                  'RETURN end.id AS id, length(path) AS distance';
                                  
                    -- Execute Cypher query
                    RETURN QUERY
                    SELECT 
                        (row->>'id')::TEXT,
                        (row->>'distance')::INTEGER
                    FROM
                        cypher('test_rag_graph', cypher_query, {}, true) AS (row agtype);
                END;
                $$ LANGUAGE plpgsql;
                
                -- Grant permissions
                GRANT EXECUTE ON FUNCTION graph_traverse TO PUBLIC;
            """))
            
            yield conn
            
            # Cleanup after tests
            await conn.execute(text("""
                DROP TABLE IF EXISTS test_rag_documents CASCADE;
                DROP TABLE IF EXISTS test_rag_categories CASCADE;
                DROP TABLE IF EXISTS test_rag_embeddings CASCADE;
                SELECT * FROM ag_catalog.drop_graph('test_rag_graph', true);
            """))
    
    @pytest.fixture
    async def graph_setup(self, db_setup):
        """Set up graph structure and load test data into the graph."""
        conn = db_setup
        
        # Create metadata with tables
        metadata = MetaData()
        categories = Table("test_rag_categories", metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String),
            Column("description", String)
        )
        documents = Table("test_rag_documents", metadata,
            Column("id", Integer, primary_key=True),
            Column("title", String),
            Column("content", String),
            Column("category_id", Integer, ForeignKey("test_rag_categories.id"))
        )
        
        # Create emitters for both tables
        category_emitter = GraphSQLEmitter(table=categories, schema="public")
        document_emitter = GraphSQLEmitter(table=documents, schema="public")
        
        # Generate SQL for graph integration
        for stmt in category_emitter.generate_sql() + document_emitter.generate_sql():
            await conn.execute(text(stmt.sql))
        
        # Add some knowledge to the graph
        knowledge_constructor = await create_knowledge_constructor(
            connection_string=f"postgresql://{conn.engine.url.username}:{conn.engine.url.password}@{conn.engine.url.host}:{conn.engine.url.port}/{conn.engine.url.database}",
            graph_name="test_rag_graph"
        )
        
        # Create text sources with knowledge
        sources = [
            TextSource(
                id="source1",
                content="""Python is a high-level programming language created by Guido van Rossum. 
                           It is known for its simplicity and readability. Python is widely used for 
                           web development, data science, and machine learning."""
            ),
            TextSource(
                id="source2",
                content="""Machine learning is a subset of artificial intelligence. It allows computers 
                           to learn from data without explicit programming. Many companies use machine 
                           learning for recommendation systems and predictive analytics."""
            ),
            TextSource(
                id="source3",
                content="""Climate change is causing more extreme weather events worldwide. Rising global 
                           temperatures lead to melting ice caps, rising sea levels, and disruption of 
                           ecosystems. Reducing carbon emissions is crucial to mitigate these effects."""
            )
        ]
        
        # Construct knowledge graph
        await knowledge_constructor.construct_knowledge_graph(sources)
        
        yield conn
        
        # Knowledge constructor cleanup
        await knowledge_constructor.close()
    
    @pytest.fixture
    async def graph_navigator(self, db_setup):
        """Create a graph navigator for testing."""
        conn = db_setup
        
        navigator = await create_graph_navigator(
            connection_string=f"postgresql://{conn.engine.url.username}:{conn.engine.url.password}@{conn.engine.url.host}:{conn.engine.url.port}/{conn.engine.url.database}",
            graph_name="test_rag_graph"
        )
        
        yield navigator
        
        await navigator.close()
    
    @pytest.fixture
    async def vector_search_service(self, db_setup):
        """Create a vector search service for testing."""
        conn = db_setup
        
        # Create the service
        service = VectorSearchService(
            entity_type=TestEntity,
            table_name="test_rag_embeddings",
            schema="public"
        )
        
        yield service
    
    @pytest.fixture
    async def knowledge_constructor(self, db_setup):
        """Create a knowledge constructor for testing."""
        conn = db_setup
        
        constructor = await create_knowledge_constructor(
            connection_string=f"postgresql://{conn.engine.url.username}:{conn.engine.url.password}@{conn.engine.url.host}:{conn.engine.url.port}/{conn.engine.url.database}",
            graph_name="test_rag_graph"
        )
        
        yield constructor
        
        await constructor.close()
    
    @pytest.fixture
    async def graph_rag_service(self, db_setup, graph_navigator, vector_search_service, knowledge_constructor):
        """Create a graph RAG service for testing."""
        conn = db_setup
        
        # Create the GraphRAGService
        service = GraphRAGService(
            vector_search=vector_search_service,
            graph_navigator=graph_navigator,
            knowledge_constructor=knowledge_constructor
        )
        
        yield service
    
    @pytest.mark.asyncio
    async def test_extract_relevant_nodes(self, graph_setup, graph_rag_service):
        """Test extracting relevant nodes from vector search."""
        # Query for programming-related content
        relevant_nodes = await graph_rag_service.extract_relevant_nodes(
            query="python programming",
            limit=3,
            threshold=0.1  # Low threshold for test purposes
        )
        
        # Should find at least document 1 (Python) and possibly document 2 (ML)
        assert len(relevant_nodes) > 0
        assert "1" in relevant_nodes  # Python document
    
    @pytest.mark.asyncio
    async def test_retrieve_knowledge_context(self, graph_setup, graph_rag_service):
        """Test retrieving context from knowledge graph."""
        # Query for climate change
        contexts = await graph_rag_service.retrieve_knowledge_context(
            query="climate",
            limit=5
        )
        
        # Should find climate change information
        assert len(contexts) > 0
        
        # At least one context should contain "climate" or "Climate"
        climate_found = False
        for context in contexts:
            if "climate" in context.text.lower():
                climate_found = True
                break
        
        assert climate_found
    
    @pytest.mark.asyncio
    async def test_create_graph_enhanced_prompt(self, graph_setup, graph_rag_service):
        """Test creating a graph-enhanced RAG prompt."""
        # Create a prompt for a programming query
        result = await graph_rag_service.create_graph_enhanced_prompt(
            query="How does Python relate to machine learning?",
            system_prompt="You are a helpful AI assistant providing accurate information.",
            limit=5,
            threshold=0.1,  # Low threshold for test purposes
            max_depth=3
        )
        
        # Verify prompt structure
        assert "system_prompt" in result
        assert "user_prompt" in result
        assert result["system_prompt"] == "You are a helpful AI assistant providing accurate information."
        
        # User prompt should contain context and the query
        assert "context from a knowledge graph" in result["user_prompt"]
        assert "How does Python relate to machine learning?" in result["user_prompt"]
        
        # Should contain relevant information about Python or ML
        assert ("Python" in result["user_prompt"] or "python" in result["user_prompt"] or 
                "Machine learning" in result["user_prompt"] or "machine learning" in result["user_prompt"])
    
    @pytest.mark.asyncio
    async def test_create_hybrid_rag_prompt(self, graph_setup, graph_rag_service):
        """Test creating a hybrid RAG prompt with vector and graph content."""
        # Create a hybrid prompt
        result = await graph_rag_service.create_hybrid_rag_prompt(
            query="Tell me about climate change impacts",
            system_prompt="You are a helpful AI assistant providing accurate information.",
            vector_limit=2,
            graph_limit=2,
            threshold=0.1,  # Low threshold for test purposes
            max_depth=2
        )
        
        # Verify prompt structure
        assert "system_prompt" in result
        assert "user_prompt" in result
        assert result["system_prompt"] == "You are a helpful AI assistant providing accurate information."
        
        # User prompt should contain both vector and graph sections
        assert "VECTOR SEARCH RESULTS" in result["user_prompt"]
        assert "KNOWLEDGE GRAPH CONTEXT" in result["user_prompt"]
        assert "Tell me about climate change impacts" in result["user_prompt"]
        
        # Should contain climate-related information
        assert "climate" in result["user_prompt"].lower() or "environment" in result["user_prompt"].lower()
    
    @pytest.mark.asyncio
    async def test_factory_function(self, db_setup, graph_setup):
        """Test the factory function for creating a GraphRAGService."""
        conn = db_setup
        
        # Use the factory function
        service = await create_graph_rag_service(
            connection_string=f"postgresql://{conn.engine.url.username}:{conn.engine.url.password}@{conn.engine.url.host}:{conn.engine.url.port}/{conn.engine.url.database}",
            entity_type=TestEntity,
            table_name="test_rag_embeddings",
            graph_name="test_rag_graph"
        )
        
        # Verify that service is created correctly
        assert isinstance(service, GraphRAGService)
        assert service.vector_search is not None
        assert service.graph_navigator is not None
        assert service.knowledge_constructor is not None
        
        # Test basic functionality
        nodes = await service.extract_relevant_nodes(
            query="python programming",
            limit=2,
            threshold=0.1
        )
        
        assert len(nodes) > 0