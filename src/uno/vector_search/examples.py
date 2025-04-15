"""
Example usage of vector search features in the Uno framework.

This module provides complete examples of using the vector search features
including creating, searching, and updating vector embeddings.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, ConfigDict

from uno.database.session import async_session, get_db
from uno.dependencies import get_service_provider
from uno.domain.vector_search import VectorQuery, VectorSearchResult


class DocumentExample(BaseModel):
    """
    Example document model for vector search demonstrations.

    This model represents a simple document with title, content, and
    tag fields that can be used to demonstrate vector search capabilities.
    """

    id: Optional[str] = None
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


async def create_example_documents() -> List[str]:
    """
    Create example documents for vector search demonstration.

    This function inserts example documents into the database with
    various content to demonstrate different types of searches.

    Returns:
        List of created document IDs
    """
    # Get the database connection
    async with async_session() as session:
        from sqlalchemy import text
        from uno.settings import uno_settings

        # Delete any existing example documents
        await session.execute(
            text(
                f"""
            DELETE FROM {uno_settings.DB_SCHEMA}.documents 
            WHERE title LIKE 'Example: %'
            """
            )
        )
        await session.commit()

        # Define example documents
        example_docs = [
            DocumentExample(
                title="Example: Python Programming Basics",
                content="""
                Python is a high-level, interpreted programming language known for its simplicity and readability.
                This document covers Python basics including variables, data types, control flow, and functions.
                
                Variables in Python are created when you assign a value to a name:
                x = 5
                name = "Python"
                
                Python has several built-in data types:
                - Numeric types: int, float, complex
                - Sequence types: list, tuple, range
                - Mapping type: dict
                - Set types: set, frozenset
                - Boolean type: bool
                - Binary types: bytes, bytearray, memoryview
                
                Control flow statements include if-else, for loops, and while loops:
                
                if x > 5:
                    print("x is greater than 5")
                else:
                    print("x is not greater than 5")
                
                Functions are defined using the def keyword:
                
                def greet(name):
                    return f"Hello, {name}!"
                """,
                tags=["python", "programming", "tutorial"],
            ),
            DocumentExample(
                title="Example: Introduction to Machine Learning",
                content="""
                Machine learning is a field of artificial intelligence that enables systems to learn 
                and improve from experience without being explicitly programmed.
                
                Key concepts in machine learning include:
                
                1. Supervised Learning: Training a model on labeled data to make predictions
                   - Classification: Predicting categorical labels
                   - Regression: Predicting continuous values
                
                2. Unsupervised Learning: Finding patterns in unlabeled data
                   - Clustering: Grouping similar instances
                   - Dimensionality Reduction: Simplifying data representation
                
                3. Reinforcement Learning: Learning through interaction with an environment
                
                Common machine learning algorithms include:
                - Linear Regression
                - Logistic Regression
                - Decision Trees
                - Random Forests
                - Support Vector Machines
                - K-means Clustering
                - Neural Networks
                
                The machine learning workflow typically involves:
                1. Data collection and preparation
                2. Feature engineering
                3. Model selection and training
                4. Evaluation
                5. Deployment
                """,
                tags=["machine learning", "AI", "data science"],
            ),
            DocumentExample(
                title="Example: Introduction to Vector Search",
                content="""
                Vector search is a technique used to find similar items in a large dataset based on their 
                vector representations or embeddings.
                
                Key concepts in vector search:
                
                1. Embeddings: Dense vector representations of data that capture semantic meaning
                   - Text embeddings represent words or documents in a high-dimensional space
                   - Image embeddings represent visual features
                   - Audio embeddings represent sound patterns
                
                2. Similarity metrics:
                   - Cosine similarity: Measures the cosine of the angle between vectors
                   - Euclidean distance (L2): Measures the straight-line distance
                   - Dot product: Measures the product of magnitudes and cosine similarity
                
                3. Approximate Nearest Neighbor (ANN) algorithms:
                   - HNSW (Hierarchical Navigable Small World): Graph-based search
                   - IVF (Inverted File Index): Partition-based search
                   - PQ (Product Quantization): Compression-based search
                
                Vector search is used in:
                - Recommendation systems
                - Semantic search
                - Duplicate detection
                - Image similarity
                - Retrieval-Augmented Generation (RAG)
                """,
                tags=["vector search", "embeddings", "similarity"],
            ),
            DocumentExample(
                title="Example: PostgreSQL Database Management",
                content="""
                PostgreSQL is a powerful, open-source object-relational database system with over 
                30 years of active development.
                
                Key features of PostgreSQL:
                
                1. ACID Compliance: Ensures reliability and data integrity
                   - Atomicity: Transactions are all-or-nothing
                   - Consistency: Database remains in a consistent state
                   - Isolation: Transactions don't interfere with each other
                   - Durability: Committed transactions remain permanent
                
                2. Advanced features:
                   - Complex queries
                   - Foreign keys
                   - Triggers
                   - Views
                   - Transactional integrity
                   - Multi-version concurrency control (MVCC)
                
                3. Extensibility:
                   - Custom data types
                   - Custom functions
                   - Procedural languages
                   - Extensions
                
                PostgreSQL extensions include:
                - PostGIS for spatial data
                - TimescaleDB for time-series data
                - pgVector for vector similarity search
                - Apache AGE for graph database capabilities
                
                PostgreSQL supports advanced indexing methods:
                - B-tree (default)
                - Hash
                - GiST
                - SP-GiST
                - GIN
                - BRIN
                """,
                tags=["postgresql", "database", "SQL"],
            ),
            DocumentExample(
                title="Example: Web Development with FastAPI",
                content="""
                FastAPI is a modern, fast web framework for building APIs with Python based on 
                standard Python type hints.
                
                Key features of FastAPI:
                
                1. Performance: FastAPI is one of the fastest Python frameworks available
                
                2. Easy to use:
                   - Based on standard Python type hints
                   - Automatic validation of request data
                   - Automatic generation of OpenAPI and JSON Schema documentation
                
                3. Modern Python features:
                   - Async/await support
                   - Type annotations
                   - Dependency injection
                
                Example FastAPI application:
                
                ```python
                from fastapi import FastAPI, Query, Path, Depends
                from pydantic import BaseModel
                
                app = FastAPI()
                
                class Item(BaseModel):
                    name: str
                    price: float
                    
                @app.get("/items/{item_id}")
                async def read_item(
                    item_id: int = Path(..., gt=0),
                    q: str = Query(None, max_length=50)
                ):
                    return {"item_id": item_id, "q": q}
                    
                @app.post("/items/")
                async def create_item(item: Item):
                    return item
                ```
                
                FastAPI includes built-in support for:
                - JSON Schema validation
                - OAuth2 with JWT tokens
                - WebSockets
                - Background tasks
                - Testing with pytest
                """,
                tags=["fastapi", "web development", "API"],
            ),
        ]

        # Insert the documents
        document_ids = []
        for doc in example_docs:
            # Insert the document
            insert_stmt = text(
                f"""
            INSERT INTO {uno_settings.DB_SCHEMA}.documents
                (title, content, metadata)
            VALUES
                (:title, :content, :metadata)
            RETURNING id
            """
            )

            # Convert tags to metadata JSON
            metadata = {"tags": doc.tags}

            result = await session.execute(
                insert_stmt,
                {"title": doc.title, "content": doc.content, "metadata": metadata},
            )

            # Get the ID of the inserted document
            doc_id = result.scalar()
            document_ids.append(doc_id)

        # Commit the transaction
        await session.commit()

        return document_ids


async def simple_vector_search_example(
    query_text: str, limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Perform a simple vector search on the example documents.

    Args:
        query_text: The search query
        limit: Maximum number of results to return

    Returns:
        List of search results with ID, title, similarity score, and snippet
    """
    provider = get_service_provider()
    search_service = provider.get_vector_search_service(
        entity_type="document", table_name="documents"
    )

    # Create a query object
    query = VectorQuery(
        query_text=query_text,
        limit=limit,
        threshold=0.5,  # Lower threshold to get more results
    )

    # Execute the search
    results = await search_service.search(query)

    # Format the results
    formatted_results = []
    for result in results:
        # Extract data from the row data
        row_data = {}
        if hasattr(result, "entity") and result.entity:
            # Use entity data if loaded
            row_data = {"title": result.entity.title, "content": result.entity.content}
        else:
            # Otherwise use metadata
            row_data = result.metadata.get("row_data", {})

        # Get content snippet (first 150 characters)
        content = row_data.get("content", "")
        snippet = content[:150] + "..." if len(content) > 150 else content

        # Format the result
        formatted_results.append(
            {
                "id": result.id,
                "title": row_data.get("title", "Untitled"),
                "similarity": f"{result.similarity:.2f}",
                "snippet": snippet,
            }
        )

    return formatted_results


async def batch_update_example() -> Dict[str, int]:
    """
    Demonstrate batch updating of vector embeddings.

    This function updates all document embeddings in a batch operation,
    useful for initial loading or refreshing embeddings.

    Returns:
        Statistics about the batch update operation
    """
    provider = get_service_provider()
    batch_update_service = provider.get_batch_vector_update_service()

    # Update all documents
    stats = await batch_update_service.update_all_entities(
        entity_type="documents", content_fields=["title", "content"]
    )

    return stats


async def rag_prompt_example(query: str) -> Dict[str, str]:
    """
    Demonstrate RAG prompt generation.

    This function shows how to create a prompt for a large language model
    that includes relevant context from vector search results.

    Args:
        query: The user's question

    Returns:
        Dictionary with system_prompt and user_prompt for an LLM
    """
    provider = get_service_provider()
    rag_service = provider.get_rag_service(
        entity_type="document", table_name="documents"
    )

    # Define a system prompt
    system_prompt = """You are a helpful assistant that answers questions based on the provided context.
If the context doesn't contain the information needed to answer the question, say that you don't know.
Keep your answers concise and directly address the user's question."""

    # Create a RAG prompt with the query and system prompt
    prompt = await rag_service.create_rag_prompt(
        query=query,
        system_prompt=system_prompt,
        limit=3,  # Number of documents to retrieve
        threshold=0.6,  # Similarity threshold
    )

    return prompt


async def run_all_examples():
    """Run all vector search examples and print results."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Creating example documents...")
    document_ids = await create_example_documents()
    logger.info(f"Created {len(document_ids)} example documents")

    # Sleep briefly to ensure embeddings are generated
    await asyncio.sleep(2)

    logger.info("\nPerforming vector search...")
    search_results = await simple_vector_search_example(
        "How does PostgreSQL support vector search?", limit=3
    )
    logger.info("Search results:")
    for i, result in enumerate(search_results, 1):
        logger.info(f"{i}. {result['title']} (Score: {result['similarity']})")
        logger.info(f"   {result['snippet']}")

    logger.info("\nGenerating RAG prompt...")
    prompt = await rag_prompt_example(
        "Explain how FastAPI handles parameter validation"
    )
    logger.info("System prompt:")
    logger.info(prompt["system_prompt"])
    logger.info("\nUser prompt (with RAG context):")
    logger.info(prompt["user_prompt"])

    logger.info("\nRunning batch embedding update...")
    stats = await batch_update_example()
    logger.info(f"Batch update stats: {stats}")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
