"""
Tests for selective relationship loading functionality.

This module tests the selective relationship loading features
of the Uno database layer, which improve performance by only loading
relationships that are needed.
"""

import pytest
import asyncio
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, MagicMock, patch

import pytest

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.relationship_loader import (
    RelationshipLoader,
    RelationshipCache,
    RelationshipCacheConfig,
    lazy_load,
    LazyRelationship,
    invalidate_entity_cache,
)


Base = declarative_base()


# Define test models
class Author(Base):
    __tablename__ = "authors"

    id = Column(String, primary_key=True)
    name = Column(String)

    # Define relationships
    books = relationship("Book", back_populates="author")

    # Define relationships metadata
    __relationships__ = {
        "books": {
            "field": "books",
            "target_type": "Book",
            "is_collection": True,
            "foreign_key": "author_id",
        }
    }


class Book(Base):
    __tablename__ = "books"

    id = Column(String, primary_key=True)
    title = Column(String)
    author_id = Column(String, ForeignKey("authors.id"))

    # Define relationships
    author = relationship("Author", back_populates="books")
    reviews = relationship("Review", back_populates="book")

    # Define relationships metadata
    __relationships__ = {
        "author": {
            "field": "author",
            "target_type": "Author",
            "is_collection": False,
            "foreign_key": "id",
        },
        "reviews": {
            "field": "reviews",
            "target_type": "Review",
            "is_collection": True,
            "foreign_key": "book_id",
        },
    }


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True)
    text = Column(String)
    rating = Column(Integer)
    book_id = Column(String, ForeignKey("books.id"))

    # Define relationships
    book = relationship("Book", back_populates="reviews")

    # Define relationships metadata
    __relationships__ = {
        "book": {
            "field": "book",
            "target_type": "Book",
            "is_collection": False,
            "foreign_key": "id",
        }
    }


# Model with lazy loading
class LazyLoadingBook:
    def __init__(self, id, title, author_id):
        self.id = id
        self.title = title
        self.author_id = author_id
        self._author = None
        self._reviews = None

    # Define lazy loading properties
    @lazy_load("author")
    def author(self):
        """Author relationship with lazy loading."""
        pass

    @lazy_load("reviews")
    def reviews(self):
        """Reviews relationship with lazy loading."""
        pass


@pytest.fixture
def mock_session():
    """Mock AsyncSession."""
    session = MagicMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_author():
    """Mock author record."""
    return {
        "id": "author1",
        "name": "Jane Doe",
    }


@pytest.fixture
def mock_books():
    """Mock book records."""
    return [
        {"id": "book1", "title": "Book One", "author_id": "author1"},
        {"id": "book2", "title": "Book Two", "author_id": "author1"},
    ]


@pytest.fixture
def mock_reviews():
    """Mock review records."""
    return [
        {"id": "review1", "text": "Great book", "rating": 5, "book_id": "book1"},
        {"id": "review2", "text": "Decent book", "rating": 3, "book_id": "book1"},
        {"id": "review3", "text": "Excellent book", "rating": 5, "book_id": "book2"},
    ]


class TestRelationshipLoader:
    """Tests for the RelationshipLoader class."""

    def test_get_relationships(self):
        """Test retrieving relationship metadata."""
        # Setup
        loader = RelationshipLoader(Book)

        # Execute
        relationships = loader._get_relationships()

        # Assert
        assert "author" in relationships
        assert "reviews" in relationships
        assert relationships["author"]["is_collection"] is False
        assert relationships["reviews"]["is_collection"] is True

    async def test_load_to_one_relationship(self, mock_session, mock_author):
        """Test loading a to-one relationship."""
        # Setup
        book = {"id": "book1", "title": "Test Book", "author_id": "author1"}

        # Mock session execute response
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_author
        mock_session.execute.return_value = result

        # Execute
        loader = RelationshipLoader(Book)
        with patch("uno.database.relationship_loader.select"):
            book_with_author = await loader._load_entity_relationships(
                book, ["author"], mock_session
            )

        # Assert
        assert book_with_author["author"] == mock_author
        assert mock_session.execute.call_count == 1

    async def test_load_to_many_relationship(self, mock_session, mock_reviews):
        """Test loading a to-many relationship."""
        # Setup
        book = {"id": "book1", "title": "Test Book", "author_id": "author1"}

        # Filter reviews for this book
        book1_reviews = [r for r in mock_reviews if r["book_id"] == "book1"]

        # Mock session execute response
        result = MagicMock()
        result.scalars().all.return_value = book1_reviews
        mock_session.execute.return_value = result

        # Execute
        loader = RelationshipLoader(Book)
        with patch("uno.database.relationship_loader.select"):
            book_with_reviews = await loader._load_entity_relationships(
                book, ["reviews"], mock_session
            )

        # Assert
        assert book_with_reviews["reviews"] == book1_reviews
        assert mock_session.execute.call_count == 1

    async def test_load_relationships_batch(
        self, mock_session, mock_author, mock_reviews
    ):
        """Test batch loading of relationships."""
        # Setup
        books = [
            {"id": "book1", "title": "Book One", "author_id": "author1"},
            {"id": "book2", "title": "Book Two", "author_id": "author1"},
        ]

        # Mock to-one relationship loading
        authors_result = MagicMock()
        authors_result.scalars().all.return_value = [mock_author]

        # Mock to-many relationship loading
        reviews_result = MagicMock()
        reviews_result.scalars().all.return_value = mock_reviews

        # Set up session execute to return different results based on the query
        mock_session.execute.side_effect = [authors_result, reviews_result]

        # Execute
        loader = RelationshipLoader(Book)
        with patch("uno.database.relationship_loader.select"):
            books_with_relations = await loader._load_batch_relationships(
                books, ["author", "reviews"], mock_session
            )

        # Assert
        assert len(books_with_relations) == 2
        assert all("author" in book for book in books_with_relations)
        assert all("reviews" in book for book in books_with_relations)
        assert books_with_relations[0]["author"] == mock_author
        assert books_with_relations[1]["author"] == mock_author
        assert len(books_with_relations[0]["reviews"]) == 2  # book1 has 2 reviews
        assert len(books_with_relations[1]["reviews"]) == 1  # book2 has 1 review
        assert mock_session.execute.call_count == 2  # One call per relationship type


class TestRelationshipCache:
    """Tests for the RelationshipCache class."""

    async def test_to_one_relationship_cache(self, mock_session, mock_author):
        """Test caching of to-one relationships."""
        # Setup
        cache_config = RelationshipCacheConfig(
            enabled=True, default_ttl=60.0, cache_to_one=True
        )

        # Create a cache with mocked query cache
        mock_query_cache = MagicMock()
        mock_query_cache.get = AsyncMock(
            return_value=MagicMock(is_success=False)
        )  # First call is a miss
        mock_query_cache.set = AsyncMock()

        cache = RelationshipCache(config=cache_config, query_cache=mock_query_cache)

        # Create a book entity
        book = {
            "id": "book1",
            "title": "Test Book",
            "author_id": "author1",
            "__class__": MagicMock().__class__,
        }

        # Mock the relationship fetch
        # First call is a cache miss, return from DB
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_author
        mock_session.execute.return_value = result

        # Execute - First load (cache miss)
        loader = RelationshipLoader(Book, cache=cache)
        with patch("uno.database.relationship_loader.select"):
            book_with_author = await loader._load_entity_relationships(
                book, ["author"], mock_session
            )

        # Assert the first load works and caches
        assert book_with_author["author"] == mock_author
        assert mock_session.execute.call_count == 1
        assert mock_query_cache.set.call_count == 1

        # Setup for second load (cache hit)
        mock_query_cache.get = AsyncMock(
            return_value=MagicMock(is_success=True, value=mock_author)
        )

        # Clear the book's loaded relationship
        book.pop("author", None)

        # Reset session mock to verify it's not called again
        mock_session.reset_mock()

        # Execute - Second load (cache hit)
        with patch("uno.database.relationship_loader.select"):
            book_with_author = await loader._load_entity_relationships(
                book, ["author"], mock_session
            )

        # Assert the second load uses the cache
        assert book_with_author["author"] == mock_author
        assert mock_session.execute.call_count == 0  # No DB query
        assert cache.hits == 1  # Cache hit counter incremented

    async def test_to_many_relationship_cache(self, mock_session, mock_reviews):
        """Test caching of to-many relationships."""
        # Setup
        cache_config = RelationshipCacheConfig(
            enabled=True, default_ttl=60.0, cache_to_many=True
        )

        # Create a cache with mocked query cache
        mock_query_cache = MagicMock()
        mock_query_cache.get = AsyncMock(
            return_value=MagicMock(is_success=False)
        )  # First call is a miss
        mock_query_cache.set = AsyncMock()

        cache = RelationshipCache(config=cache_config, query_cache=mock_query_cache)

        # Create a book entity
        book = {
            "id": "book1",
            "title": "Test Book",
            "author_id": "author1",
            "__class__": MagicMock().__class__,
        }

        # Filter reviews for this book
        book1_reviews = [r for r in mock_reviews if r["book_id"] == "book1"]
        for review in book1_reviews:
            review["__class__"] = MagicMock().__class__
            review["__tablename__"] = "reviews"

        # Mock the relationship fetch
        # First call is a cache miss, return from DB
        result = MagicMock()
        result.scalars().all.return_value = book1_reviews
        mock_session.execute.return_value = result

        # Execute - First load (cache miss)
        loader = RelationshipLoader(Book, cache=cache)
        with patch("uno.database.relationship_loader.select"):
            book_with_reviews = await loader._load_entity_relationships(
                book, ["reviews"], mock_session
            )

        # Assert the first load works and caches
        assert book_with_reviews["reviews"] == book1_reviews
        assert mock_session.execute.call_count == 1
        assert mock_query_cache.set.call_count == 1

        # Setup for second load (cache hit)
        mock_query_cache.get = AsyncMock(
            return_value=MagicMock(is_success=True, value=book1_reviews)
        )

        # Clear the book's loaded relationship
        book.pop("reviews", None)

        # Reset session mock to verify it's not called again
        mock_session.reset_mock()

        # Execute - Second load (cache hit)
        with patch("uno.database.relationship_loader.select"):
            book_with_reviews = await loader._load_entity_relationships(
                book, ["reviews"], mock_session
            )

        # Assert the second load uses the cache
        assert book_with_reviews["reviews"] == book1_reviews
        assert mock_session.execute.call_count == 0  # No DB query
        assert cache.hits == 1  # Cache hit counter incremented

    async def test_batch_relationship_cache(
        self, mock_session, mock_author, mock_reviews
    ):
        """Test batch loading with caching."""
        # Setup
        cache_config = RelationshipCacheConfig(
            enabled=True, default_ttl=60.0, cache_to_one=True, cache_to_many=True
        )

        # Create a cache with mocked query cache
        mock_query_cache = MagicMock()
        # All initial calls will be cache misses
        mock_query_cache.get = AsyncMock(return_value=MagicMock(is_success=False))
        mock_query_cache.set = AsyncMock()

        cache = RelationshipCache(config=cache_config, query_cache=mock_query_cache)

        # Create book entities
        books = [
            {
                "id": "book1",
                "title": "Book One",
                "author_id": "author1",
                "__class__": MagicMock().__class__,
            },
            {
                "id": "book2",
                "title": "Book Two",
                "author_id": "author1",
                "__class__": MagicMock().__class__,
            },
        ]

        # Add class attribute to author for mock tablename
        mock_author["__class__"] = MagicMock().__class__
        mock_author["__tablename__"] = "authors"

        # Add class attribute to reviews for mock tablename
        for review in mock_reviews:
            review["__class__"] = MagicMock().__class__
            review["__tablename__"] = "reviews"

        # Mock to-one relationship loading
        authors_result = MagicMock()
        authors_result.scalars().all.return_value = [mock_author]

        # Mock to-many relationship loading
        reviews_result = MagicMock()
        reviews_result.scalars().all.return_value = mock_reviews

        # Set up session execute to return different results based on the query
        mock_session.execute.side_effect = [authors_result, reviews_result]

        # Execute - First load (cache miss)
        loader = RelationshipLoader(Book, cache=cache)
        with patch("uno.database.relationship_loader.select"):
            books_with_relations = await loader._load_batch_relationships(
                books, ["author", "reviews"], mock_session
            )

        # Assert the first load worked
        assert len(books_with_relations) == 2
        assert all("author" in book for book in books_with_relations)
        assert all("reviews" in book for book in books_with_relations)
        assert mock_session.execute.call_count == 2  # One call per relationship type
        assert mock_query_cache.set.call_count > 0  # Should have cached results

        # Setup for second load with the same books
        # But with cache hits for all relationships
        def get_mock_side_effect(*args, **kwargs):
            # For author relationship (to-one)
            if "rel:one:" in str(args):
                return MagicMock(is_success=True, value=mock_author)
            # For reviews relationship (to-many)
            elif "rel:many:" in str(args):
                book_id = None
                if "book1" in str(args):
                    book_id = "book1"
                elif "book2" in str(args):
                    book_id = "book2"

                if book_id:
                    book_reviews = [r for r in mock_reviews if r["book_id"] == book_id]
                    return MagicMock(is_success=True, value=book_reviews)

            # Default cache miss
            return MagicMock(is_success=False)

        # Setup cache to return hits
        mock_query_cache.get = AsyncMock(side_effect=get_mock_side_effect)

        # Reset the books
        for book in books:
            book.pop("author", None)
            book.pop("reviews", None)

        # Reset session mock to verify it's not called again
        mock_session.reset_mock()

        # Execute - Second load (cache hit)
        with patch("uno.database.relationship_loader.select"):
            books_with_relations = await loader._load_batch_relationships(
                books, ["author", "reviews"], mock_session
            )

        # Assert the second load uses the cache
        assert len(books_with_relations) == 2
        assert all("author" in book for book in books_with_relations)
        assert all("reviews" in book for book in books_with_relations)
        assert mock_session.execute.call_count == 0  # No DB query
        assert cache.hits > 0  # Cache hits recorded

    async def test_invalidate_relationships(self):
        """Test invalidation of cached relationships."""
        # Setup
        cache_config = RelationshipCacheConfig(enabled=True, default_ttl=60.0)

        # Create a cache with mocked query cache
        mock_query_cache = MagicMock()
        mock_query_cache.invalidate_by_table = AsyncMock()
        mock_query_cache.invalidate = AsyncMock()

        cache = RelationshipCache(config=cache_config, query_cache=mock_query_cache)

        # Create a book entity to invalidate
        book = {
            "id": "book1",
            "title": "Test Book",
            "__class__": type("DummyClass", (), {"__tablename__": "books"}),
        }

        # Execute - Invalidate the book entity
        loader = RelationshipLoader(Book, cache=cache)
        await loader.invalidate_relationships(book)

        # Assert
        assert (
            mock_query_cache.invalidate_by_table.call_count == 1
        )  # Should invalidate by table
        assert (
            mock_query_cache.invalidate.call_count == 1
        )  # Should invalidate specific to-one relationships
        assert cache.invalidations == 1  # Invalidation counter incremented


class TestLazyLoading:
    """Tests for the lazy loading functionality."""

    async def test_lazy_relationship_proxy(self, mock_session, mock_author):
        """Test the LazyRelationship proxy."""
        # Setup
        book = LazyLoadingBook("book1", "Test Book", "author1")

        # Mock loader behavior
        mock_loader = MagicMock()
        mock_loader._load_entity_relationships = AsyncMock(
            return_value={
                "id": "book1",
                "title": "Test Book",
                "author_id": "author1",
                "author": mock_author,
            }
        )
        mock_loader.relationships = {}  # Add empty relationships to trigger fallback
        mock_loader.cache = MagicMock()

        # Create relationship proxy
        proxy = LazyRelationship(book, "author", "_author")

        # Execute
        with (
            patch(
                "uno.database.relationship_loader.RelationshipLoader",
                return_value=mock_loader,
            ),
            patch("uno.database.relationship_loader.enhanced_async_session"),
        ):
            loaded_author = await proxy.load()

        # Assert
        assert loaded_author == mock_author
        assert book._author == mock_author
        assert proxy._loaded is True

    async def test_lazy_relationship_with_cache(self, mock_session, mock_author):
        """Test lazy loading with caching."""
        # Setup
        book = LazyLoadingBook("book1", "Test Book", "author1")

        # Mock loader behavior
        mock_loader = MagicMock()
        mock_loader.relationships = {
            "author": {
                "field": "author",
                "target_type": "Author",
                "is_collection": False,
                "foreign_key": "id",
            }
        }

        # Mock cache behavior - first a miss, then a hit
        mock_cache = MagicMock()
        mock_cache.get_to_one = AsyncMock(
            return_value=MagicMock(is_success=True, value=mock_author)
        )
        mock_loader.cache = mock_cache

        # Create relationship proxy
        proxy = LazyRelationship(book, "author", "_author")

        # Execute
        with patch(
            "uno.database.relationship_loader.RelationshipLoader",
            return_value=mock_loader,
        ):
            loaded_author = await proxy.load()

        # Assert
        assert loaded_author == mock_author
        assert book._author == mock_author
        assert proxy._loaded is True
        assert mock_cache.get_to_one.call_count == 1  # Should check cache


# Helper for mocking async methods
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
