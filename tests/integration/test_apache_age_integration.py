"""
Integration tests for Apache AGE graph database integration.

This module contains integration tests that verify the proper functioning of
Apache AGE graph database features in the Uno framework, including automatic
synchronization between relational tables and graph data.
"""

import pytest
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple

from sqlalchemy import Table, Column, Integer, String, ForeignKey, text, MetaData
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession

from uno.sql.emitters.graph import GraphSQLEmitter
from uno.domain.graph_path_query import GraphPathQuery, GraphPathQueryService, PathQuerySpecification
from uno.ai.graph_integration.graph_navigator import create_graph_navigator, GraphNavigator
from uno.ai.graph_integration.knowledge_constructor import create_knowledge_constructor, KnowledgeConstructor, TextSource


Base = declarative_base()


class Person(Base):
    """Test entity representing a person."""
    
    __tablename__ = "test_persons"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    city_id = Column(Integer, ForeignKey("test_cities.id"))
    
    city = relationship("City", back_populates="residents")
    
    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.name}', age={self.age})>"


class City(Base):
    """Test entity representing a city."""
    
    __tablename__ = "test_cities"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    country = Column(String)
    
    residents = relationship("Person", back_populates="city")
    
    def __repr__(self):
        return f"<City(id={self.id}, name='{self.name}', country='{self.country}')>"


class TestApacheAgeIntegration:
    """Integration tests for Apache AGE graph database features."""
    
    @pytest.fixture(scope="module")
    async def db_session(self, connection_pool):
        """Create a database session for testing."""
        async with connection_pool.connect() as conn:
            # Create test tables
            await conn.execute(text("""
                DROP TABLE IF EXISTS test_persons CASCADE;
                DROP TABLE IF EXISTS test_cities CASCADE;
                
                CREATE TABLE test_cities (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    country VARCHAR(100) NOT NULL
                );
                
                CREATE TABLE test_persons (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    age INTEGER NOT NULL,
                    city_id INTEGER REFERENCES test_cities(id)
                );
            """))
            
            # Load AGE extension
            await conn.execute(text("LOAD 'age';"))
            
            # Create or reset graph
            await conn.execute(text("""
                SELECT * FROM ag_catalog.drop_graph('test_graph', true);
                SELECT * FROM ag_catalog.create_graph('test_graph');
            """))
            
            yield conn
            
            # Cleanup after tests
            await conn.execute(text("""
                DROP TABLE IF EXISTS test_persons CASCADE;
                DROP TABLE IF EXISTS test_cities CASCADE;
                SELECT * FROM ag_catalog.drop_graph('test_graph', true);
            """))
    
    @pytest.fixture
    async def emitter(self):
        """Create a graph SQL emitter for testing."""
        from uno.settings import uno_settings
        
        # Create metadata with tables
        metadata = MetaData()
        cities = Table("test_cities", metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String),
            Column("country", String)
        )
        persons = Table("test_persons", metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String),
            Column("age", Integer),
            Column("city_id", Integer, ForeignKey("test_cities.id"))
        )
        
        # Create emitter for Person table
        emitter = GraphSQLEmitter(
            table=persons,
            schema=uno_settings.DB_SCHEMA
        )
        
        # Create emitter for City table
        city_emitter = GraphSQLEmitter(
            table=cities,
            schema=uno_settings.DB_SCHEMA
        )
        
        return emitter, city_emitter
    
    @pytest.fixture
    async def test_data(self, db_session):
        """Insert test data for the integration tests."""
        # Insert test cities
        await db_session.execute(text("""
            INSERT INTO test_cities (id, name, country) VALUES 
            (1, 'New York', 'USA'),
            (2, 'London', 'UK'),
            (3, 'Tokyo', 'Japan');
        """))
        
        # Insert test persons
        await db_session.execute(text("""
            INSERT INTO test_persons (id, name, age, city_id) VALUES 
            (1, 'John Smith', 35, 1),
            (2, 'Emma Wilson', 28, 2),
            (3, 'Michael Brown', 42, 1),
            (4, 'Sophia Lee', 31, 3);
        """))
    
    @pytest.fixture
    async def graph_navigator(self, db_session, connection_pool):
        """Create a graph navigator for testing."""
        from uno.settings import uno_settings
        
        connection_string = f"postgresql://{uno_settings.DB_USER}:{uno_settings.DB_PASSWORD}@{uno_settings.DB_HOST}:{uno_settings.DB_PORT}/{uno_settings.DB_NAME}"
        
        navigator = await create_graph_navigator(
            connection_string=connection_string,
            graph_name="test_graph"
        )
        
        yield navigator
        
        await navigator.close()
    
    @pytest.fixture
    async def knowledge_constructor(self, db_session, connection_pool):
        """Create a knowledge constructor for testing."""
        from uno.settings import uno_settings
        
        connection_string = f"postgresql://{uno_settings.DB_USER}:{uno_settings.DB_PASSWORD}@{uno_settings.DB_HOST}:{uno_settings.DB_PORT}/{uno_settings.DB_NAME}"
        
        constructor = await create_knowledge_constructor(
            connection_string=connection_string,
            graph_name="test_graph"
        )
        
        yield constructor
        
        await constructor.close()
    
    @pytest.mark.asyncio
    async def test_graph_sql_generation(self, emitter):
        """Test generation of graph SQL for triggers and functions."""
        person_emitter, city_emitter = emitter
        
        # Generate SQL for both tables
        person_statements = person_emitter.generate_sql()
        city_statements = city_emitter.generate_sql()
        
        # Check that all required statements are generated
        statement_types = ["create_labels", "create_insert_function", "create_insert_trigger",
                         "create_update_function", "create_update_trigger", 
                         "create_delete_function", "create_delete_trigger",
                         "create_truncate_function", "create_truncate_trigger"]
        
        for stmt_type in statement_types:
            assert any(stmt.name == stmt_type for stmt in person_statements)
            assert any(stmt.name == stmt_type for stmt in city_statements)
        
        # Check that SQL contains proper graph labels
        create_labels_sql = next(stmt for stmt in person_statements if stmt.name == "create_labels").sql
        assert "TestPerson" in create_labels_sql  # Should use CamelCase for label
        
        # Check that SQL contains proper column handling
        update_function_sql = next(stmt for stmt in person_statements if stmt.name == "create_update_function").sql
        assert "NEW.name" in update_function_sql
        assert "NEW.age" in update_function_sql
        assert "NEW.city_id" in update_function_sql
    
    @pytest.mark.asyncio
    async def test_graph_synchronization(self, db_session, emitter, test_data):
        """Test automatic synchronization between relational tables and graph database."""
        person_emitter, city_emitter = emitter
        
        # Generate and execute SQL to create graph functions and triggers
        for stmt in person_emitter.generate_sql() + city_emitter.generate_sql():
            await db_session.execute(text(stmt.sql))
        
        # Now the triggers should be active - insert new data
        await db_session.execute(text("""
            INSERT INTO test_cities (id, name, country) VALUES 
            (4, 'Paris', 'France');
            
            INSERT INTO test_persons (id, name, age, city_id) VALUES 
            (5, 'Alice Johnson', 29, 4);
        """))
        
        # Verify nodes were created in the graph
        async def verify_graph_nodes():
            result = await db_session.execute(text("""
                LOAD 'age';
                SET graph_path = test_graph;
                SELECT * FROM cypher('test_graph', $$
                    MATCH (p:TestPerson)
                    WHERE p.id = '5'
                    RETURN p
                $$) AS (node agtype);
            """))
            
            rows = result.fetchall()
            assert len(rows) > 0
            
            # Check city node
            result = await db_session.execute(text("""
                LOAD 'age';
                SET graph_path = test_graph;
                SELECT * FROM cypher('test_graph', $$
                    MATCH (c:TestCity)
                    WHERE c.id = '4'
                    RETURN c
                $$) AS (node agtype);
            """))
            
            rows = result.fetchall()
            assert len(rows) > 0
        
        await verify_graph_nodes()
        
        # Test relationship creation
        async def verify_graph_relationships():
            result = await db_session.execute(text("""
                LOAD 'age';
                SET graph_path = test_graph;
                SELECT * FROM cypher('test_graph', $$
                    MATCH (p:TestPerson)-[r:CITY_ID]->(c:TestCity)
                    WHERE p.id = '5' AND c.id = '4'
                    RETURN r
                $$) AS (rel agtype);
            """))
            
            rows = result.fetchall()
            assert len(rows) > 0
        
        await verify_graph_relationships()
        
        # Test update synchronization
        await db_session.execute(text("""
            UPDATE test_persons SET name = 'Alice Smith', age = 30 WHERE id = 5;
        """))
        
        # Verify node was updated
        async def verify_node_update():
            result = await db_session.execute(text("""
                LOAD 'age';
                SET graph_path = test_graph;
                SELECT * FROM cypher('test_graph', $$
                    MATCH (p:TestPerson)
                    WHERE p.id = '5'
                    RETURN p
                $$) AS (node agtype);
            """))
            
            rows = result.fetchall()
            node_data = json.loads(rows[0][0])
            
            # The node name property should be updated in the properties JSON
            properties = node_data.get("properties", {})
            assert properties.get("name") == "Alice Smith"
        
        await verify_node_update()
        
        # Test delete synchronization
        await db_session.execute(text("""
            DELETE FROM test_persons WHERE id = 5;
        """))
        
        # Verify node was deleted
        async def verify_node_deletion():
            result = await db_session.execute(text("""
                LOAD 'age';
                SET graph_path = test_graph;
                SELECT * FROM cypher('test_graph', $$
                    MATCH (p:TestPerson)
                    WHERE p.id = '5'
                    RETURN p
                $$) AS (node agtype);
            """))
            
            rows = result.fetchall()
            assert len(rows) == 0
        
        await verify_node_deletion()
    
    @pytest.mark.asyncio
    async def test_graph_path_query(self, db_session, emitter, test_data):
        """Test graph path queries using the GraphPathQuery class."""
        person_emitter, city_emitter = emitter
        
        # Generate and execute SQL to create graph functions and triggers
        for stmt in person_emitter.generate_sql() + city_emitter.generate_sql():
            await db_session.execute(text(stmt.sql))
        
        # Create a graph path query
        graph_query = GraphPathQuery(track_performance=True, use_cache=True)
        
        # Define a path query to find people in New York
        query_spec = PathQuerySpecification(
            path="(p:TestPerson)-[:CITY_ID]->(c:TestCity)",
            params={"c.name": "New York"}
        )
        
        # Execute the query
        entity_ids, metadata = await graph_query.execute(query_spec)
        
        # Should find two people in New York
        assert len(entity_ids) == 2
        assert "1" in entity_ids  # John Smith
        assert "3" in entity_ids  # Michael Brown
        
        # Verify metadata
        assert metadata.query_path == "(p:TestPerson)-[:CITY_ID]->(c:TestCity)"
        assert metadata.record_count == 2
        
        # Try a more complex query
        query_spec = PathQuerySpecification(
            path="(p:TestPerson)-[:CITY_ID]->(c:TestCity)",
            params={"c.country": "USA", "p.age": {"lookup": "gt", "val": 30}}
        )
        
        # Execute the query
        entity_ids, metadata = await graph_query.execute(query_spec)
        
        # Should find John Smith (age 35) but not Michael Brown (age 42)
        assert len(entity_ids) == 2
        assert "1" in entity_ids  # John Smith
        assert "3" in entity_ids  # Michael Brown (age 42)
    
    @pytest.mark.asyncio
    async def test_graph_navigation(self, db_session, emitter, test_data, graph_navigator):
        """Test advanced graph navigation using the GraphNavigator class."""
        person_emitter, city_emitter = emitter
        
        # Generate and execute SQL to create graph functions and triggers
        for stmt in person_emitter.generate_sql() + city_emitter.generate_sql():
            await db_session.execute(text(stmt.sql))
        
        # Get IDs from the database
        result = await db_session.execute(text("""
            SELECT id FROM test_persons WHERE name = 'John Smith';
        """))
        john_id = str(result.scalar())
        
        result = await db_session.execute(text("""
            SELECT id FROM test_persons WHERE name = 'Michael Brown';
        """))
        michael_id = str(result.scalar())
        
        # Extract a subgraph centered around John Smith
        subgraph = await graph_navigator.extract_subgraph(
            center_node_id=john_id,
            max_depth=2,
            relationship_types=["CITY_ID"]
        )
        
        # Should find John and the city of New York, plus Michael who also lives in New York
        assert subgraph is not None
        assert subgraph.center_node["id"] == john_id
        assert len(subgraph.nodes) >= 3  # John, New York, Michael
        assert len(subgraph.relationships) >= 2  # John-New York, Michael-New York
        
        # Find paths between people (through cities)
        # John Smith in New York and Emma Wilson in London
        path = await graph_navigator.find_path_with_reasoning(
            start_node_id=john_id,
            end_node_id=michael_id,
            reasoning_type="causal",
            max_depth=3,
            relationship_types=["CITY_ID"]
        )
        
        # Should find a path through New York City
        assert path is not None
        assert path.start_node["id"] == john_id
        assert path.end_node["id"] == michael_id
    
    @pytest.mark.asyncio
    async def test_knowledge_construction(self, db_session, knowledge_constructor):
        """Test knowledge graph construction using the KnowledgeConstructor class."""
        # Create text sources with knowledge about cities and people
        sources = [
            TextSource(
                id="source1",
                content="New York City is located in the United States. John Smith is a resident of New York City."
            ),
            TextSource(
                id="source2",
                content="London is the capital of the United Kingdom. Emma Wilson lives in London."
            )
        ]
        
        # Construct a knowledge graph
        result = await knowledge_constructor.construct_knowledge_graph(sources)
        
        # Check that construction was successful
        assert result.success is True
        assert len(result.source_ids) == 2
        
        # Should have created entities and relationships
        assert result.entity_count > 0
        assert result.relationship_count > 0
        
        # Query the graph to find New York
        results = await knowledge_constructor.query_graph("""
            MATCH (loc)
            WHERE loc.properties->>'text' CONTAINS 'New York'
            RETURN loc
        """)
        
        # Should find New York
        assert len(results) > 0
        
        # Find relationship between John Smith and New York
        results = await knowledge_constructor.query_graph("""
            MATCH (person)-[r]-(loc)
            WHERE person.properties->>'text' CONTAINS 'John Smith'
            AND loc.properties->>'text' CONTAINS 'New York'
            RETURN r
        """)
        
        # Should find at least one relationship
        assert len(results) > 0