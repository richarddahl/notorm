"""
Method Naming Standards for the Uno Framework.

This module documents the standardized method naming conventions used throughout 
the Uno framework, ensuring consistent and predictable APIs.
"""

# ============================================================================
# Repository Methods
# ============================================================================

# Core CRUD Operations
# -------------------
# get(id) - Get an entity by ID
# list(filters, order_by, limit, offset) - List entities with optional filtering and pagination
# add(entity) - Add a new entity
# update(entity) - Update an existing entity
# delete(entity) - Delete an entity
# exists(id) - Check if an entity with the given ID exists
# save(entity) - Save an entity (add if new, update if existing)

# Batch Operations
# ---------------
# add_many(entities) - Add multiple entities
# update_many(entities) - Update multiple entities
# delete_many(entities) - Delete multiple entities
# delete_by_ids(ids) - Delete entities by their IDs

# Specification Pattern
# -------------------
# find(specification) - Find entities matching a specification
# find_one(specification) - Find a single entity matching a specification
# count(specification) - Count entities matching a specification

# Streaming Operations
# ------------------
# stream(filters, order_by, batch_size) - Stream entities matching filter criteria

# ============================================================================
# Service Methods
# ============================================================================

# Core Service Operation
# --------------------
# execute(input_data) - Execute the service operation
# validate(input_data) - Validate input data

# Domain Service Operations
# ----------------------
# execute(input_data, context) - Execute the domain service with context
# _execute_internal(input_data, context) - Internal implementation of the service

# CRUD Service Operations
# ---------------------
# get(id) - Get an entity by ID
# list(filters, order_by, limit, offset) - List entities with filtering and pagination
# create(data) - Create a new entity from data
# update(id, data) - Update an existing entity with new data
# delete(id) - Delete an entity by ID

# Query Service Operations
# ---------------------
# execute_query(params) - Execute a query operation
# count(filters) - Count entities matching filters

# ============================================================================
# Method Naming Standards by Action
# ============================================================================

# Creation Methods
# --------------
# create_* - Create a new resource
# add_* - Add a resource to a collection

# Retrieval Methods
# ---------------
# get_* - Get a specific resource by ID
# find_* - Find resources matching criteria
# list_* - List multiple resources

# Update Methods
# ------------
# update_* - Update an existing resource
# modify_* - Partially modify a resource

# Deletion Methods
# -------------
# delete_* - Delete a resource
# remove_* - Remove a resource from a collection

# Query Methods
# -----------
# query_* - General purpose query method
# search_* - Search for resources by keyword/criteria
# filter_* - Filter resources by criteria
# count_* - Count resources

# Conversion Methods
# ---------------
# to_* - Convert to another format
# from_* - Convert from another format
# parse_* - Parse input into a structured format

# Validation Methods
# ---------------
# validate_* - Validate data
# is_valid_* - Check if something is valid
# check_* - Check a condition

# Process Methods
# ------------
# process_* - Process data
# execute_* - Execute an operation
# run_* - Run a process
# perform_* - Perform an action

# ============================================================================
# Standardization Rules
# ============================================================================

# 1. Use verb prefixes consistently for similar operations
# 2. Follow get_*/set_* pattern for properties
# 3. Use find_* for search operations
# 4. Use list_* for retrieving multiple items
# 5. Use create_* for resource creation
# 6. Use update_* for updating resources
# 7. Use delete_* for removing resources