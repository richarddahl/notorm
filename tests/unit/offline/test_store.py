"""Tests for the offline store module."""

import unittest
import uuid
from unittest import IsolatedAsyncioTestCase
from typing import Dict, Any, List

from uno.offline.store import (
    OfflineStore, 
    StorageOptions, 
    CollectionSchema,
    IndexDefinition,
    RelationshipDefinition
)


class TestOfflineStore(IsolatedAsyncioTestCase):
    """Tests for the OfflineStore class."""
    
    async def asyncSetUp(self):
        """Set up the test environment."""
        # Define schemas for test collections
        user_schema = CollectionSchema(
            name="users",
            key_path="id",
            indexes=[
                IndexDefinition(name="email_idx", key_path="email", unique=True),
                IndexDefinition(name="name_idx", key_path="name")
            ]
        )
        
        order_schema = CollectionSchema(
            name="orders",
            key_path="id",
            indexes=[
                IndexDefinition(name="user_id_idx", key_path="user_id"),
                IndexDefinition(name="date_idx", key_path="date")
            ],
            relationships=[
                RelationshipDefinition(
                    name="user",
                    collection="users",
                    type="many-to-one",
                    foreign_key="user_id"
                )
            ]
        )
        
        order_item_schema = CollectionSchema(
            name="order_items",
            key_path="id",
            indexes=[
                IndexDefinition(name="order_id_idx", key_path="order_id")
            ],
            relationships=[
                RelationshipDefinition(
                    name="order",
                    collection="orders",
                    type="many-to-one",
                    foreign_key="order_id"
                )
            ]
        )
        
        # Create storage options with in-memory backend
        self.options = StorageOptions(
            storage_backend="memory",
            database_name="test_db",
            collections=[user_schema, order_schema, order_item_schema]
        )
        
        # Create and initialize the offline store
        self.store = OfflineStore(self.options)
        await self.store.initialize()
    
    async def asyncTearDown(self):
        """Clean up after the test."""
        await self.store.close()
    
    async def test_create_and_get(self):
        """Test creating and getting a record."""
        # Create a user
        user = {
            "id": "user1",
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        # Create the record
        user_id = await self.store.create("users", user)
        
        # Verify the ID
        self.assertEqual(user_id, "user1")
        
        # Get the record
        retrieved_user = await self.store.get("users", "user1")
        
        # Verify the record
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user["id"], "user1")
        self.assertEqual(retrieved_user["name"], "John Doe")
        self.assertEqual(retrieved_user["email"], "john@example.com")
    
    async def test_create_batch(self):
        """Test creating multiple records in a batch."""
        # Create multiple users
        users = [
            {"id": "user1", "name": "John Doe", "email": "john@example.com"},
            {"id": "user2", "name": "Jane Smith", "email": "jane@example.com"},
            {"id": "user3", "name": "Bob Johnson", "email": "bob@example.com"}
        ]
        
        # Create the records
        user_ids = await self.store.create_batch("users", users)
        
        # Verify the IDs
        self.assertEqual(len(user_ids), 3)
        self.assertEqual(user_ids[0], "user1")
        self.assertEqual(user_ids[1], "user2")
        self.assertEqual(user_ids[2], "user3")
        
        # Get the count
        count = await self.store.count("users")
        self.assertEqual(count, 3)
    
    async def test_update(self):
        """Test updating a record."""
        # Create a user
        user = {
            "id": "user1",
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        await self.store.create("users", user)
        
        # Update the user
        updated_user = {
            "id": "user1",
            "name": "John Smith",
            "email": "john.smith@example.com"
        }
        
        result = await self.store.update("users", updated_user)
        
        # Verify the result
        self.assertTrue(result)
        
        # Get the updated record
        retrieved_user = await self.store.get("users", "user1")
        
        # Verify the record
        self.assertEqual(retrieved_user["name"], "John Smith")
        self.assertEqual(retrieved_user["email"], "john.smith@example.com")
    
    async def test_update_batch(self):
        """Test updating multiple records in a batch."""
        # Create multiple users
        users = [
            {"id": "user1", "name": "John Doe", "email": "john@example.com"},
            {"id": "user2", "name": "Jane Smith", "email": "jane@example.com"},
            {"id": "user3", "name": "Bob Johnson", "email": "bob@example.com"}
        ]
        
        await self.store.create_batch("users", users)
        
        # Update users
        updates = [
            {"id": "user1", "role": "admin"},
            {"id": "user2", "role": "editor"},
            {"id": "user3", "role": "viewer"}
        ]
        
        count = await self.store.update_batch("users", updates)
        
        # Verify count
        self.assertEqual(count, 3)
        
        # Verify updates
        user1 = await self.store.get("users", "user1")
        user2 = await self.store.get("users", "user2")
        user3 = await self.store.get("users", "user3")
        
        self.assertEqual(user1["role"], "admin")
        self.assertEqual(user2["role"], "editor")
        self.assertEqual(user3["role"], "viewer")
    
    async def test_delete(self):
        """Test deleting a record."""
        # Create a user
        user = {
            "id": "user1",
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        await self.store.create("users", user)
        
        # Verify it exists
        retrieved_user = await self.store.get("users", "user1")
        self.assertIsNotNone(retrieved_user)
        
        # Delete the user
        result = await self.store.delete("users", "user1")
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify it's gone
        retrieved_user = await self.store.get("users", "user1")
        self.assertIsNone(retrieved_user)
    
    async def test_delete_batch(self):
        """Test deleting multiple records in a batch."""
        # Create multiple users
        users = [
            {"id": "user1", "name": "John Doe", "email": "john@example.com"},
            {"id": "user2", "name": "Jane Smith", "email": "jane@example.com"},
            {"id": "user3", "name": "Bob Johnson", "email": "bob@example.com"}
        ]
        
        await self.store.create_batch("users", users)
        
        # Delete users
        count = await self.store.delete_batch("users", ["user1", "user3"])
        
        # Verify count
        self.assertEqual(count, 2)
        
        # Verify deletions
        user1 = await self.store.get("users", "user1")
        user2 = await self.store.get("users", "user2")
        user3 = await self.store.get("users", "user3")
        
        self.assertIsNone(user1)
        self.assertIsNotNone(user2)
        self.assertIsNone(user3)
    
    async def test_query(self):
        """Test querying records."""
        # Create multiple users
        users = [
            {"id": "user1", "name": "John Doe", "email": "john@example.com", "role": "admin"},
            {"id": "user2", "name": "Jane Smith", "email": "jane@example.com", "role": "editor"},
            {"id": "user3", "name": "Bob Johnson", "email": "bob@example.com", "role": "editor"},
            {"id": "user4", "name": "Alice Brown", "email": "alice@example.com", "role": "viewer"}
        ]
        
        await self.store.create_batch("users", users)
        
        # Query all users
        result = await self.store.query("users")
        self.assertEqual(result.total, 4)
        self.assertEqual(len(result.items), 4)
        
        # Query by role
        result = await self.store.query("users", {"filters": {"role": "editor"}})
        self.assertEqual(result.total, 2)
        self.assertEqual(len(result.items), 2)
        
        # Query with sorting
        result = await self.store.query("users", {"sort": [{"field": "name", "direction": "asc"}]})
        self.assertEqual(result.items[0]["name"], "Alice Brown")
        self.assertEqual(result.items[1]["name"], "Bob Johnson")
        self.assertEqual(result.items[2]["name"], "Jane Smith")
        self.assertEqual(result.items[3]["name"], "John Doe")
        
        # Query with limit and offset
        result = await self.store.query("users", {"sort": [{"field": "name", "direction": "asc"}], "limit": 2, "offset": 1})
        self.assertEqual(result.total, 4)
        self.assertEqual(len(result.items), 2)
        self.assertEqual(result.items[0]["name"], "Bob Johnson")
        self.assertEqual(result.items[1]["name"], "Jane Smith")
        
        # Query with complex filter
        result = await self.store.query("users", {"filters": {"role": {"$ne": "admin"}}})
        self.assertEqual(result.total, 3)
    
    async def test_relationships(self):
        """Test querying with relationships."""
        # Create users and orders
        users = [
            {"id": "user1", "name": "John Doe", "email": "john@example.com"},
            {"id": "user2", "name": "Jane Smith", "email": "jane@example.com"}
        ]
        
        await self.store.create_batch("users", users)
        
        orders = [
            {"id": "order1", "user_id": "user1", "date": "2023-01-01", "total": 100},
            {"id": "order2", "user_id": "user1", "date": "2023-01-15", "total": 200},
            {"id": "order3", "user_id": "user2", "date": "2023-01-10", "total": 150}
        ]
        
        await self.store.create_batch("orders", orders)
        
        order_items = [
            {"id": "item1", "order_id": "order1", "product": "Product A", "quantity": 2, "price": 50},
            {"id": "item2", "order_id": "order2", "product": "Product B", "quantity": 1, "price": 200},
            {"id": "item3", "order_id": "order3", "product": "Product A", "quantity": 3, "price": 50}
        ]
        
        await self.store.create_batch("order_items", order_items)
        
        # Get order with user
        order = await self.store.get("orders", "order1", include=["user"])
        self.assertIsNotNone(order)
        self.assertIn("user", order)
        self.assertEqual(order["user"]["name"], "John Doe")
        
        # Query orders for a user
        result = await self.store.query("orders", {"filters": {"user_id": "user1"}})
        self.assertEqual(result.total, 2)
    
    async def test_transaction(self):
        """Test transactions."""
        # Start a transaction
        transaction = await self.store.begin_transaction(["users", "orders"])
        
        try:
            # Create a user
            user = {"id": "user1", "name": "John Doe", "email": "john@example.com"}
            await transaction.create("users", user)
            
            # Create an order
            order = {"id": "order1", "user_id": "user1", "date": "2023-01-01", "total": 100}
            await transaction.create("orders", order)
            
            # Commit the transaction
            await transaction.commit()
        except Exception:
            # Rollback on error
            await transaction.rollback()
            raise
        
        # Verify records were created
        user = await self.store.get("users", "user1")
        order = await self.store.get("orders", "order1")
        
        self.assertIsNotNone(user)
        self.assertIsNotNone(order)
        
        # Start another transaction that will be rolled back
        transaction = await self.store.begin_transaction(["users"])
        
        # Update user
        user["name"] = "John Smith"
        await transaction.update("users", user)
        
        # Verify the update is visible within the transaction
        user_in_transaction = await transaction.read("users", "user1")
        self.assertEqual(user_in_transaction["name"], "John Smith")
        
        # Rollback the transaction
        await transaction.rollback()
        
        # Verify the update was rolled back
        user = await self.store.get("users", "user1")
        self.assertEqual(user["name"], "John Doe")
    
    async def test_clear(self):
        """Test clearing collections."""
        # Create users
        users = [
            {"id": "user1", "name": "John Doe", "email": "john@example.com"},
            {"id": "user2", "name": "Jane Smith", "email": "jane@example.com"}
        ]
        
        await self.store.create_batch("users", users)
        
        # Create orders
        orders = [
            {"id": "order1", "user_id": "user1", "date": "2023-01-01", "total": 100}
        ]
        
        await self.store.create_batch("orders", orders)
        
        # Verify records exist
        self.assertEqual(await self.store.count("users"), 2)
        self.assertEqual(await self.store.count("orders"), 1)
        
        # Clear users
        await self.store.clear(["users"])
        
        # Verify users are gone but orders remain
        self.assertEqual(await self.store.count("users"), 0)
        self.assertEqual(await self.store.count("orders"), 1)
        
        # Clear all collections
        await self.store.clear()
        
        # Verify all records are gone
        self.assertEqual(await self.store.count("users"), 0)
        self.assertEqual(await self.store.count("orders"), 0)
    
    async def test_storage_info(self):
        """Test getting storage info."""
        # Create some data
        users = [
            {"id": "user1", "name": "John Doe", "email": "john@example.com"},
            {"id": "user2", "name": "Jane Smith", "email": "jane@example.com"}
        ]
        
        await self.store.create_batch("users", users)
        
        # Get storage info
        info = await self.store.get_storage_info()
        
        # Verify info
        self.assertIn("total_records", info)
        self.assertIn("collection_usage", info)
        self.assertIn("users", info["collection_usage"])
        self.assertEqual(info["total_records"], 2)


if __name__ == "__main__":
    unittest.main()