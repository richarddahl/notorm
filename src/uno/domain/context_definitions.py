"""
Bounded context definitions for the Uno framework.

This module defines the bounded contexts for the Uno framework and their relationships,
creating a context map that documents the strategic design of the system.
"""

from uno.domain.bounded_context import (
    BoundedContext,
    ContextRelation,
    ContextRelationType,
    get_context_map,
    register_bounded_context,
    register_context_relation,
)


def define_domain_model_context():
    """Define the Domain Model bounded context."""
    context = BoundedContext(
        name="domain_model",
        package_path="uno.domain",
        description="Core domain model components and concepts",
        responsibility="Define foundational domain patterns and business logic",
        is_core_domain=True,
        team="Core Team"
    )
    
    # Define ubiquitous language
    context.add_term("Entity", "An object defined by its identity with continuity and identity separate from its attributes")
    context.add_term("Value Object", "An immutable object with no identity, defined by its attributes")
    context.add_term("Aggregate", "A cluster of associated objects treated as a single unit for data changes")
    context.add_term("Aggregate Root", "The entry point to an aggregate that ensures the consistency of changes to the aggregate")
    context.add_term("Domain Event", "A record of something that happened in the domain")
    context.add_term("Domain Service", "A stateless operation that doesn't naturally fit within an entity or value object")
    context.add_term("Repository", "A mechanism for encapsulating storage, retrieval, and search")
    
    register_bounded_context(context)
    return context


def define_database_context():
    """Define the Database bounded context."""
    context = BoundedContext(
        name="database",
        package_path="uno.database",
        description="Database access and persistence mechanisms",
        responsibility="Provide data access services to the application",
        is_core_domain=False,
        team="Infrastructure Team"
    )
    
    # Define ubiquitous language
    context.add_term("Session", "A unit of work with the database")
    context.add_term("Transaction", "An atomic unit of work that either completely succeeds or completely fails")
    context.add_term("Connection", "A link to the database server")
    context.add_term("Query", "A request for data from the database")
    context.add_term("Migration", "A controlled change to the database schema")
    
    register_bounded_context(context)
    return context


def define_schema_context():
    """Define the Schema bounded context."""
    context = BoundedContext(
        name="schema",
        package_path="uno.schema",
        description="Schema definition and validation",
        responsibility="Define and validate data structures",
        is_core_domain=False,
        team="Core Team"
    )
    
    # Define ubiquitous language
    context.add_term("Schema", "A formal definition of the structure of data")
    context.add_term("Validation", "The process of ensuring data conforms to a schema")
    context.add_term("Type", "A classification identifying the kind of data")
    context.add_term("Constraint", "A rule that restricts the values that data can have")
    
    register_bounded_context(context)
    return context


def define_api_context():
    """Define the API bounded context."""
    context = BoundedContext(
        name="api",
        package_path="uno.api",
        description="API definition and exposure",
        responsibility="Expose domain capabilities via a defined API",
        is_core_domain=False,
        team="API Team"
    )
    
    # Define ubiquitous language
    context.add_term("Endpoint", "A specific URL where an API can be accessed")
    context.add_term("Route", "A mapping from an API path to a handler function")
    context.add_term("Request", "An incoming message to the API")
    context.add_term("Response", "An outgoing message from the API")
    context.add_term("Authentication", "The process of verifying the identity of a client")
    context.add_term("Authorization", "The process of determining if a client has access rights")
    
    register_bounded_context(context)
    return context


def define_authorization_context():
    """Define the Authorization bounded context."""
    context = BoundedContext(
        name="authorization",
        package_path="uno.authorization",
        description="Access control and security",
        responsibility="Define and enforce access control policies",
        is_core_domain=True,
        team="Security Team"
    )
    
    # Define ubiquitous language
    context.add_term("Permission", "A specific access right to a resource")
    context.add_term("Role", "A named collection of permissions")
    context.add_term("User", "An entity that can be authenticated and authorized")
    context.add_term("Policy", "A set of rules defining access control")
    context.add_term("Authentication", "The process of verifying a user's identity")
    context.add_term("Authorization", "The process of determining if a user has access rights")
    
    register_bounded_context(context)
    return context


def define_query_context():
    """Define the Query bounded context."""
    context = BoundedContext(
        name="query",
        package_path="uno.queries",
        description="Query generation and execution",
        responsibility="Provide query capabilities to the application",
        is_core_domain=False,
        team="Data Team"
    )
    
    # Define ubiquitous language
    context.add_term("Query", "A request for data based on specific criteria")
    context.add_term("Filter", "A condition that restricts the results of a query")
    context.add_term("Sort", "The ordering of query results")
    context.add_term("Pagination", "The division of query results into pages")
    context.add_term("Field Selection", "The selection of specific fields from query results")
    
    register_bounded_context(context)
    return context


def define_sql_context():
    """Define the SQL Generation bounded context."""
    context = BoundedContext(
        name="sql",
        package_path="uno.sql",
        description="SQL statement generation",
        responsibility="Generate SQL statements for database operations",
        is_core_domain=False,
        team="Data Team"
    )
    
    # Define ubiquitous language
    context.add_term("Statement", "A SQL command to be executed")
    context.add_term("Query", "A SQL statement that retrieves data")
    context.add_term("Expression", "A SQL fragment that evaluates to a value")
    context.add_term("Table", "A set of data organized in rows and columns")
    context.add_term("Join", "A SQL operation that combines rows from two or more tables")
    
    register_bounded_context(context)
    return context


def define_meta_context():
    """Define the Meta bounded context."""
    context = BoundedContext(
        name="meta",
        package_path="uno.meta",
        description="Metadata and introspection",
        responsibility="Provide metadata and introspection capabilities",
        is_core_domain=False,
        team="Core Team"
    )
    
    # Define ubiquitous language
    context.add_term("Metadata", "Data that describes other data")
    context.add_term("Type", "A classification identifying the kind of data")
    context.add_term("Record", "A structured piece of metadata")
    context.add_term("Introspection", "The ability to examine the structure of an object at runtime")
    
    register_bounded_context(context)
    return context


def define_context_relationships(contexts):
    """
    Define relationships between bounded contexts.
    
    Args:
        contexts: Dictionary of contexts by name
    """
    # Define domain model's relationships
    register_context_relation(ContextRelation(
        source_context="domain_model",
        target_context="database",
        relation_type=ContextRelationType.UPSTREAM_DOWNSTREAM,
        description="Domain model defines entities that database must persist",
        implementation_notes="Repository interfaces defined in domain, implemented in database"
    ))
    
    register_context_relation(ContextRelation(
        source_context="domain_model",
        target_context="schema",
        relation_type=ContextRelationType.SHARED_KERNEL,
        description="Domain model and schema share core concepts for data validation",
        implementation_notes="Both contexts use common validation mechanisms"
    ))
    
    register_context_relation(ContextRelation(
        source_context="domain_model",
        target_context="api",
        relation_type=ContextRelationType.UPSTREAM_DOWNSTREAM,
        description="Domain model defines concepts that API exposes",
        implementation_notes="API translates domain model to/from external representation"
    ))
    
    # Define database's relationships
    register_context_relation(ContextRelation(
        source_context="database",
        target_context="sql",
        relation_type=ContextRelationType.CONFORMIST,
        description="Database conforms to SQL context's model of SQL statements",
        implementation_notes="Database uses SQL context to generate statements"
    ))
    
    # Define schema's relationships
    register_context_relation(ContextRelation(
        source_context="schema",
        target_context="api",
        relation_type=ContextRelationType.UPSTREAM_DOWNSTREAM,
        description="Schema context defines validation used by API",
        implementation_notes="API uses schema context for request/response validation"
    ))
    
    # Define API's relationships
    register_context_relation(ContextRelation(
        source_context="api",
        target_context="authorization",
        relation_type=ContextRelationType.ANTICORRUPTION_LAYER,
        description="API uses an anti-corruption layer to protect itself from changes in authorization",
        implementation_notes="API translates authorization concepts to/from its own model"
    ))
    
    # Define query's relationships
    register_context_relation(ContextRelation(
        source_context="query",
        target_context="sql",
        relation_type=ContextRelationType.ANTICORRUPTION_LAYER,
        description="Query context uses an anti-corruption layer to translate to SQL",
        implementation_notes="Prevents SQL details from leaking into query language"
    ))
    
    register_context_relation(ContextRelation(
        source_context="query",
        target_context="domain_model",
        relation_type=ContextRelationType.OPEN_HOST_SERVICE,
        description="Query context provides a well-defined API for the domain model",
        implementation_notes="Domain model uses query context through a stable interface"
    ))
    
    # Define authorization's relationships
    register_context_relation(ContextRelation(
        source_context="authorization",
        target_context="meta",
        relation_type=ContextRelationType.UPSTREAM_DOWNSTREAM,
        description="Authorization defines security rules that meta must respect",
        implementation_notes="Meta context conforms to authorization model"
    ))
    
    # Define meta's relationships
    register_context_relation(ContextRelation(
        source_context="meta",
        target_context="domain_model",
        relation_type=ContextRelationType.OPEN_HOST_SERVICE,
        description="Meta context provides introspection services to domain model",
        implementation_notes="Domain model uses meta through a stable interface"
    ))


def initialize_context_map():
    """Initialize the context map with all bounded contexts and relationships."""
    # Define all contexts
    contexts = {
        "domain_model": define_domain_model_context(),
        "database": define_database_context(),
        "schema": define_schema_context(),
        "api": define_api_context(),
        "authorization": define_authorization_context(),
        "query": define_query_context(),
        "sql": define_sql_context(),
        "meta": define_meta_context()
    }
    
    # Define relationships between contexts
    define_context_relationships(contexts)
    
    # Return the context map
    return get_context_map()


# Initialize context map on module import
context_map = initialize_context_map()


def get_dot_graph():
    """
    Get a DOT graph representation of the context map.
    
    Returns:
        DOT graph string that can be rendered with Graphviz
    """
    return context_map.generate_dot_graph()


def analyze_dependencies():
    """
    Analyze dependencies between contexts.
    
    Returns:
        Dictionary with analysis results
    """
    return context_map.analyze_dependencies()