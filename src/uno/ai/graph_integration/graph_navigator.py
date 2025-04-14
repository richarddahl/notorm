"""
Advanced graph navigation for knowledge graphs.

This module provides sophisticated graph traversal algorithms and navigation
strategies for exploring knowledge graphs, finding paths between entities,
and retrieving relevant context for AI features.
"""

import asyncio
import json
import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable

import asyncpg
from pydantic import BaseModel, Field, validator


class TraversalMode(str, Enum):
    """Mode for graph traversal."""
    
    BREADTH_FIRST = "breadth_first"
    DEPTH_FIRST = "depth_first"
    DIJKSTRA = "dijkstra"
    A_STAR = "a_star"
    BIDIRECTIONAL = "bidirectional"
    RANDOM_WALK = "random_walk"
    PERSONALIZED_PAGERANK = "personalized_pagerank"


class NavigationAlgorithm(str, Enum):
    """Algorithm for graph navigation."""
    
    SHORTEST_PATH = "shortest_path"
    ALL_PATHS = "all_paths"
    SUBGRAPH_EXTRACTION = "subgraph_extraction"
    SIMILARITY_SEARCH = "similarity_search"
    NEIGHBORHOOD_EXPLORATION = "neighborhood_exploration"
    PATTERN_MATCHING = "pattern_matching"
    COMMUNITY_DETECTION = "community_detection"


class NavigationStrategy(str, Enum):
    """Strategy for navigating between nodes."""
    
    DEFAULT = "default"
    WEIGHTED = "weighted"
    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    FREQUENCY = "frequency"
    RELEVANCE = "relevance"
    CUSTOM = "custom"


class RelationshipType(BaseModel):
    """Definition of a relationship type in the graph."""
    
    name: str
    direction: str = "OUTGOING"  # OUTGOING, INCOMING, BOTH
    weight: float = 1.0
    max_depth: int = 3
    required: bool = False
    properties: Dict[str, Any] = Field(default_factory=dict)


class NodeFilter(BaseModel):
    """Filter for nodes in the graph."""
    
    labels: Optional[List[str]] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    exclude_labels: Optional[List[str]] = None
    exclude_properties: Dict[str, Any] = Field(default_factory=dict)
    min_degree: Optional[int] = None
    max_degree: Optional[int] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None


class PathConstraint(BaseModel):
    """Constraint for paths in the graph."""
    
    min_length: int = 1
    max_length: int = 3
    required_nodes: List[str] = Field(default_factory=list)
    excluded_nodes: List[str] = Field(default_factory=list)
    required_relationships: List[str] = Field(default_factory=list)
    excluded_relationships: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphNavigatorConfig(BaseModel):
    """Configuration for graph navigation."""
    
    age_schema: str = "ag_catalog"
    graph_name: str = "knowledge_graph"
    default_traversal_mode: TraversalMode = TraversalMode.BREADTH_FIRST
    default_algorithm: NavigationAlgorithm = NavigationAlgorithm.SHORTEST_PATH
    default_strategy: NavigationStrategy = NavigationStrategy.DEFAULT
    default_max_depth: int = 3
    default_max_results: int = 10
    relationship_types: List[RelationshipType] = Field(default_factory=list)
    default_node_filter: NodeFilter = Field(default_factory=NodeFilter)
    default_path_constraint: PathConstraint = Field(default_factory=PathConstraint)
    cache_results: bool = True
    cache_ttl: int = 3600  # seconds
    timeout: int = 30  # seconds


class PathResult(BaseModel):
    """Result of a path search in the graph."""
    
    path_id: str
    start_node: Dict[str, Any]
    end_node: Dict[str, Any]
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    length: int
    score: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubgraphResult(BaseModel):
    """Result of a subgraph extraction from the graph."""
    
    subgraph_id: str
    center_node: Dict[str, Any]
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    node_count: int
    relationship_count: int
    diameter: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphNavigator:
    """
    Advanced graph navigation for knowledge graphs.
    
    This class provides sophisticated graph traversal algorithms and navigation
    strategies for exploring knowledge graphs, finding paths between entities,
    and retrieving relevant context for AI features.
    """
    
    def __init__(
        self,
        connection_string: str,
        config: GraphNavigatorConfig,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the graph navigator.
        
        Args:
            connection_string: Database connection string
            config: Configuration for graph navigation
            logger: Optional logger
        """
        self.connection_string = connection_string
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Database connection
        self.pool = None
        
        # Result cache
        self.path_cache: Dict[str, Dict[str, PathResult]] = {}
        self.subgraph_cache: Dict[str, SubgraphResult] = {}
        
        # Cache metadata
        self.cache_timestamps: Dict[str, float] = {}
        
        # Initialization flag
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the graph navigator."""
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
        
        except Exception as e:
            self.logger.error(f"Failed to initialize graph navigator: {e}")
            raise
        
        self.initialized = True
    
    async def close(self) -> None:
        """Close the graph navigator and release resources."""
        if self.pool:
            await self.pool.close()
            self.pool = None
        
        self.initialized = False
    
    async def find_shortest_path(
        self,
        start_node_id: str,
        end_node_id: str,
        traversal_mode: Optional[TraversalMode] = None,
        relationship_types: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
        node_filter: Optional[NodeFilter] = None,
        path_constraint: Optional[PathConstraint] = None
    ) -> Optional[PathResult]:
        """
        Find the shortest path between two nodes.
        
        Args:
            start_node_id: ID of the start node
            end_node_id: ID of the end node
            traversal_mode: Mode for traversal
            relationship_types: Types of relationships to consider
            max_depth: Maximum path depth
            node_filter: Filter for nodes
            path_constraint: Constraints for paths
            
        Returns:
            Shortest path if found, None otherwise
        """
        if not self.initialized:
            await self.initialize()
        
        # Check cache first
        cache_key = f"shortest_path_{start_node_id}_{end_node_id}"
        if cache_key in self.path_cache:
            cache_time = self.cache_timestamps.get(cache_key, 0)
            if (asyncio.get_event_loop().time() - cache_time) < self.config.cache_ttl:
                return self.path_cache[cache_key].get(f"{start_node_id}_{end_node_id}")
        
        # Set default values if not provided
        traversal_mode = traversal_mode or self.config.default_traversal_mode
        max_depth = max_depth or self.config.default_max_depth
        node_filter = node_filter or self.config.default_node_filter
        path_constraint = path_constraint or self.config.default_path_constraint
        
        # Get relationship types
        rel_types = []
        if relationship_types:
            rel_types = relationship_types
        elif self.config.relationship_types:
            rel_types = [rt.name for rt in self.config.relationship_types]
        
        try:
            # Construct Cypher query based on traversal mode
            if traversal_mode == TraversalMode.BREADTH_FIRST:
                # BFS is default for shortest path
                cypher = self._build_shortest_path_query(
                    start_node_id, end_node_id, rel_types, max_depth, 
                    node_filter, path_constraint
                )
            elif traversal_mode == TraversalMode.DIJKSTRA:
                # Dijkstra's algorithm for weighted paths
                cypher = self._build_dijkstra_query(
                    start_node_id, end_node_id, rel_types, max_depth,
                    node_filter, path_constraint
                )
            elif traversal_mode == TraversalMode.A_STAR:
                # A* algorithm for heuristic-based paths
                cypher = self._build_a_star_query(
                    start_node_id, end_node_id, rel_types, max_depth,
                    node_filter, path_constraint
                )
            elif traversal_mode == TraversalMode.BIDIRECTIONAL:
                # Bidirectional search
                cypher = self._build_bidirectional_query(
                    start_node_id, end_node_id, rel_types, max_depth,
                    node_filter, path_constraint
                )
            else:
                # Default to BFS
                cypher = self._build_shortest_path_query(
                    start_node_id, end_node_id, rel_types, max_depth,
                    node_filter, path_constraint
                )
            
            # Execute query
            async with self.pool.acquire() as conn:
                # Load AGE extension
                await conn.execute(f"LOAD '{self.config.age_schema}';")
                
                # Set graph
                await conn.execute(f"SET graph_path = {self.config.graph_name};")
                
                # Execute Cypher query
                result = await conn.fetchval(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (path agtype);", 
                                          cypher, {}, True)
                
                if not result:
                    return None
                
                # Parse result
                path_data = json.loads(result)
                
                # Extract nodes and relationships
                nodes, relationships = self._extract_path_elements(path_data)
                
                # Create path result
                path_result = PathResult(
                    path_id=f"{start_node_id}_{end_node_id}",
                    start_node=nodes[0] if nodes else {},
                    end_node=nodes[-1] if nodes else {},
                    nodes=nodes,
                    relationships=relationships,
                    length=len(relationships),
                    score=1.0,
                    metadata={
                        "traversal_mode": traversal_mode,
                        "max_depth": max_depth
                    }
                )
                
                # Cache result
                if self.config.cache_results:
                    if cache_key not in self.path_cache:
                        self.path_cache[cache_key] = {}
                    
                    self.path_cache[cache_key][f"{start_node_id}_{end_node_id}"] = path_result
                    self.cache_timestamps[cache_key] = asyncio.get_event_loop().time()
                
                return path_result
        
        except Exception as e:
            self.logger.error(f"Failed to find shortest path: {e}")
            return None
    
    async def find_all_paths(
        self,
        start_node_id: str,
        end_node_id: str,
        max_paths: int = 5,
        traversal_mode: Optional[TraversalMode] = None,
        relationship_types: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
        node_filter: Optional[NodeFilter] = None,
        path_constraint: Optional[PathConstraint] = None
    ) -> List[PathResult]:
        """
        Find all paths between two nodes.
        
        Args:
            start_node_id: ID of the start node
            end_node_id: ID of the end node
            max_paths: Maximum number of paths to return
            traversal_mode: Mode for traversal
            relationship_types: Types of relationships to consider
            max_depth: Maximum path depth
            node_filter: Filter for nodes
            path_constraint: Constraints for paths
            
        Returns:
            List of paths
        """
        if not self.initialized:
            await self.initialize()
        
        # Check cache first
        cache_key = f"all_paths_{start_node_id}_{end_node_id}"
        if cache_key in self.path_cache:
            cache_time = self.cache_timestamps.get(cache_key, 0)
            if (asyncio.get_event_loop().time() - cache_time) < self.config.cache_ttl:
                return list(self.path_cache[cache_key].values())
        
        # Set default values if not provided
        traversal_mode = traversal_mode or self.config.default_traversal_mode
        max_depth = max_depth or self.config.default_max_depth
        node_filter = node_filter or self.config.default_node_filter
        path_constraint = path_constraint or self.config.default_path_constraint
        
        # Get relationship types
        rel_types = []
        if relationship_types:
            rel_types = relationship_types
        elif self.config.relationship_types:
            rel_types = [rt.name for rt in self.config.relationship_types]
        
        try:
            # Build Cypher query for all paths
            cypher = self._build_all_paths_query(
                start_node_id, end_node_id, rel_types, max_depth, 
                max_paths, node_filter, path_constraint
            )
            
            # Execute query
            async with self.pool.acquire() as conn:
                # Load AGE extension
                await conn.execute(f"LOAD '{self.config.age_schema}';")
                
                # Set graph
                await conn.execute(f"SET graph_path = {self.config.graph_name};")
                
                # Execute Cypher query
                result = await conn.fetch(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (path agtype);", 
                                       cypher, {}, True)
                
                path_results = []
                for row in result:
                    # Parse result
                    path_data = json.loads(row['path'])
                    
                    # Extract nodes and relationships
                    nodes, relationships = self._extract_path_elements(path_data)
                    
                    # Create path result
                    path_id = f"{start_node_id}_{end_node_id}_{len(path_results)}"
                    path_result = PathResult(
                        path_id=path_id,
                        start_node=nodes[0] if nodes else {},
                        end_node=nodes[-1] if nodes else {},
                        nodes=nodes,
                        relationships=relationships,
                        length=len(relationships),
                        score=1.0 / (len(relationships) + 1),  # Shorter paths score higher
                        metadata={
                            "traversal_mode": traversal_mode,
                            "max_depth": max_depth,
                            "path_index": len(path_results)
                        }
                    )
                    
                    path_results.append(path_result)
                
                # Cache results
                if self.config.cache_results:
                    if cache_key not in self.path_cache:
                        self.path_cache[cache_key] = {}
                    
                    for path in path_results:
                        self.path_cache[cache_key][path.path_id] = path
                    
                    self.cache_timestamps[cache_key] = asyncio.get_event_loop().time()
                
                return path_results
        
        except Exception as e:
            self.logger.error(f"Failed to find all paths: {e}")
            return []
    
    async def extract_subgraph(
        self,
        center_node_id: str,
        max_depth: Optional[int] = None,
        relationship_types: Optional[List[str]] = None,
        traversal_mode: Optional[TraversalMode] = None,
        node_filter: Optional[NodeFilter] = None,
        max_nodes: int = 100
    ) -> Optional[SubgraphResult]:
        """
        Extract a subgraph centered around a node.
        
        Args:
            center_node_id: ID of the center node
            max_depth: Maximum traversal depth
            relationship_types: Types of relationships to consider
            traversal_mode: Mode for traversal
            node_filter: Filter for nodes
            max_nodes: Maximum number of nodes to include
            
        Returns:
            Extracted subgraph if successful, None otherwise
        """
        if not self.initialized:
            await self.initialize()
        
        # Check cache first
        cache_key = f"subgraph_{center_node_id}_{max_depth}"
        if cache_key in self.subgraph_cache:
            cache_time = self.cache_timestamps.get(cache_key, 0)
            if (asyncio.get_event_loop().time() - cache_time) < self.config.cache_ttl:
                return self.subgraph_cache[cache_key]
        
        # Set default values if not provided
        traversal_mode = traversal_mode or self.config.default_traversal_mode
        max_depth = max_depth or self.config.default_max_depth
        node_filter = node_filter or self.config.default_node_filter
        
        # Get relationship types
        rel_types = []
        if relationship_types:
            rel_types = relationship_types
        elif self.config.relationship_types:
            rel_types = [rt.name for rt in self.config.relationship_types]
        
        try:
            # Build Cypher query for subgraph extraction
            if traversal_mode == TraversalMode.PERSONALIZED_PAGERANK:
                # Use PageRank to find most important nodes in the neighborhood
                cypher = self._build_pagerank_subgraph_query(
                    center_node_id, max_depth, rel_types, node_filter, max_nodes
                )
            else:
                # Default to neighborhood exploration
                cypher = self._build_neighborhood_query(
                    center_node_id, max_depth, rel_types, node_filter, max_nodes
                )
            
            # Execute query
            async with self.pool.acquire() as conn:
                # Load AGE extension
                await conn.execute(f"LOAD '{self.config.age_schema}';")
                
                # Set graph
                await conn.execute(f"SET graph_path = {self.config.graph_name};")
                
                # Execute Cypher query
                result = await conn.fetchval(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (subgraph agtype);", 
                                          cypher, {}, True)
                
                if not result:
                    return None
                
                # Parse result
                subgraph_data = json.loads(result)
                
                # Extract center node
                center_node = None
                for node in subgraph_data.get('nodes', []):
                    if node.get('id') == center_node_id:
                        center_node = node
                        break
                
                if not center_node:
                    self.logger.error(f"Center node {center_node_id} not found in subgraph result")
                    return None
                
                # Create subgraph result
                subgraph_result = SubgraphResult(
                    subgraph_id=f"subgraph_{center_node_id}",
                    center_node=center_node,
                    nodes=subgraph_data.get('nodes', []),
                    relationships=subgraph_data.get('relationships', []),
                    node_count=len(subgraph_data.get('nodes', [])),
                    relationship_count=len(subgraph_data.get('relationships', [])),
                    diameter=max_depth,
                    metadata={
                        "traversal_mode": traversal_mode,
                        "max_depth": max_depth,
                        "center_node_id": center_node_id
                    }
                )
                
                # Cache result
                if self.config.cache_results:
                    self.subgraph_cache[cache_key] = subgraph_result
                    self.cache_timestamps[cache_key] = asyncio.get_event_loop().time()
                
                return subgraph_result
        
        except Exception as e:
            self.logger.error(f"Failed to extract subgraph: {e}")
            return None
    
    async def find_similar_nodes(
        self,
        node_id: str,
        similarity_metric: str = "common_neighbors",
        top_k: int = 10,
        min_similarity: float = 0.0,
        relationship_types: Optional[List[str]] = None,
        node_filter: Optional[NodeFilter] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find nodes similar to a given node.
        
        Args:
            node_id: ID of the reference node
            similarity_metric: Similarity metric to use (common_neighbors, jaccard, adamic_adar)
            top_k: Maximum number of similar nodes to return
            min_similarity: Minimum similarity score
            relationship_types: Types of relationships to consider
            node_filter: Filter for nodes
            
        Returns:
            List of (node, similarity score) tuples
        """
        if not self.initialized:
            await self.initialize()
        
        # Cache key
        cache_key = f"similar_{node_id}_{similarity_metric}"
        
        # Set default values if not provided
        node_filter = node_filter or self.config.default_node_filter
        
        # Get relationship types
        rel_types = []
        if relationship_types:
            rel_types = relationship_types
        elif self.config.relationship_types:
            rel_types = [rt.name for rt in self.config.relationship_types]
        
        try:
            # Build Cypher query based on similarity metric
            if similarity_metric == "common_neighbors":
                cypher = self._build_common_neighbors_query(
                    node_id, top_k, min_similarity, rel_types, node_filter
                )
            elif similarity_metric == "jaccard":
                cypher = self._build_jaccard_similarity_query(
                    node_id, top_k, min_similarity, rel_types, node_filter
                )
            elif similarity_metric == "adamic_adar":
                cypher = self._build_adamic_adar_query(
                    node_id, top_k, min_similarity, rel_types, node_filter
                )
            else:
                # Default to common neighbors
                cypher = self._build_common_neighbors_query(
                    node_id, top_k, min_similarity, rel_types, node_filter
                )
            
            # Execute query
            async with self.pool.acquire() as conn:
                # Load AGE extension
                await conn.execute(f"LOAD '{self.config.age_schema}';")
                
                # Set graph
                await conn.execute(f"SET graph_path = {self.config.graph_name};")
                
                # Execute Cypher query
                result = await conn.fetch(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (node agtype, similarity agtype);", 
                                       cypher, {}, True)
                
                # Parse results
                similar_nodes = []
                for row in result:
                    node = json.loads(row['node'])
                    similarity = float(json.loads(row['similarity']))
                    similar_nodes.append((node, similarity))
                
                return similar_nodes
        
        except Exception as e:
            self.logger.error(f"Failed to find similar nodes: {e}")
            return []
    
    async def find_path_with_reasoning(
        self,
        start_node_id: str,
        end_node_id: str,
        reasoning_type: str = "causal",
        max_depth: Optional[int] = None,
        relationship_types: Optional[List[str]] = None
    ) -> Optional[PathResult]:
        """
        Find a path between nodes with reasoning capabilities.
        
        Args:
            start_node_id: ID of the start node
            end_node_id: ID of the end node
            reasoning_type: Type of reasoning (causal, hierarchical, temporal)
            max_depth: Maximum path depth
            relationship_types: Types of relationships to consider
            
        Returns:
            Path with reasoning information if found, None otherwise
        """
        if not self.initialized:
            await self.initialize()
        
        # Set default values if not provided
        max_depth = max_depth or self.config.default_max_depth
        
        # Get relationship types or filter based on reasoning type
        rel_types = []
        if relationship_types:
            rel_types = relationship_types
        elif reasoning_type == "causal":
            # Use causal relationship types
            rel_types = ["CAUSES", "LEADS_TO", "RESULTS_IN", "CONTRIBUTES_TO"]
        elif reasoning_type == "hierarchical":
            # Use hierarchical relationship types
            rel_types = ["IS_A", "PART_OF", "CONTAINS", "BELONGS_TO"]
        elif reasoning_type == "temporal":
            # Use temporal relationship types
            rel_types = ["BEFORE", "AFTER", "DURING", "FOLLOWS"]
        elif self.config.relationship_types:
            rel_types = [rt.name for rt in self.config.relationship_types]
        
        try:
            # Build Cypher query based on reasoning type
            if reasoning_type == "causal":
                cypher = self._build_causal_reasoning_query(
                    start_node_id, end_node_id, max_depth, rel_types
                )
            elif reasoning_type == "hierarchical":
                cypher = self._build_hierarchical_reasoning_query(
                    start_node_id, end_node_id, max_depth, rel_types
                )
            elif reasoning_type == "temporal":
                cypher = self._build_temporal_reasoning_query(
                    start_node_id, end_node_id, max_depth, rel_types
                )
            else:
                # Default to shortest path
                cypher = self._build_shortest_path_query(
                    start_node_id, end_node_id, rel_types, max_depth, 
                    self.config.default_node_filter, self.config.default_path_constraint
                )
            
            # Execute query
            async with self.pool.acquire() as conn:
                # Load AGE extension
                await conn.execute(f"LOAD '{self.config.age_schema}';")
                
                # Set graph
                await conn.execute(f"SET graph_path = {self.config.graph_name};")
                
                # Execute Cypher query
                result = await conn.fetchval(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (path agtype);", 
                                          cypher, {}, True)
                
                if not result:
                    return None
                
                # Parse result
                path_data = json.loads(result)
                
                # Extract nodes and relationships
                nodes, relationships = self._extract_path_elements(path_data)
                
                # Create path result with reasoning information
                path_result = PathResult(
                    path_id=f"{start_node_id}_{end_node_id}_reasoning",
                    start_node=nodes[0] if nodes else {},
                    end_node=nodes[-1] if nodes else {},
                    nodes=nodes,
                    relationships=relationships,
                    length=len(relationships),
                    score=1.0,
                    metadata={
                        "reasoning_type": reasoning_type,
                        "max_depth": max_depth,
                        "explanation": self._generate_path_explanation(nodes, relationships, reasoning_type)
                    }
                )
                
                return path_result
        
        except Exception as e:
            self.logger.error(f"Failed to find path with reasoning: {e}")
            return None
    
    async def detect_communities(
        self,
        algorithm: str = "louvain",
        min_community_size: int = 3,
        max_communities: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Detect communities in the graph.
        
        Args:
            algorithm: Community detection algorithm (louvain, label_propagation)
            min_community_size: Minimum size of communities to return
            max_communities: Maximum number of communities to return
            
        Returns:
            List of communities (each a dict with nodes and metadata)
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Build Cypher query based on algorithm
            if algorithm == "louvain":
                cypher = self._build_louvain_community_query(
                    min_community_size, max_communities
                )
            elif algorithm == "label_propagation":
                cypher = self._build_label_propagation_query(
                    min_community_size, max_communities
                )
            else:
                # Default to louvain
                cypher = self._build_louvain_community_query(
                    min_community_size, max_communities
                )
            
            # Execute query
            async with self.pool.acquire() as conn:
                # Load AGE extension
                await conn.execute(f"LOAD '{self.config.age_schema}';")
                
                # Set graph
                await conn.execute(f"SET graph_path = {self.config.graph_name};")
                
                # Execute Cypher query
                result = await conn.fetch(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (community agtype);", 
                                       cypher, {}, True)
                
                # Parse results
                communities = []
                for row in result:
                    community_data = json.loads(row['community'])
                    communities.append(community_data)
                
                return communities
        
        except Exception as e:
            self.logger.error(f"Failed to detect communities: {e}")
            return []
    
    async def find_context_for_rag(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        relevant_nodes: Optional[List[str]] = None,
        max_results: int = 5,
        strategy: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """
        Find graph context for retrieval-augmented generation (RAG).
        
        Args:
            query: The query text
            query_embedding: Optional embedding of the query
            relevant_nodes: Optional list of known relevant node IDs
            max_results: Maximum number of context items to return
            strategy: Context retrieval strategy (hybrid, path, neighborhood)
            
        Returns:
            List of context items with text and metadata
        """
        if not self.initialized:
            await self.initialize()
        
        context_items = []
        
        try:
            # If we have relevant nodes, use them as starting points
            if relevant_nodes and len(relevant_nodes) > 0:
                if strategy == "path":
                    # Find paths between relevant nodes
                    for i in range(len(relevant_nodes)):
                        for j in range(i+1, len(relevant_nodes)):
                            start_id = relevant_nodes[i]
                            end_id = relevant_nodes[j]
                            
                            path = await self.find_shortest_path(
                                start_node_id=start_id,
                                end_node_id=end_id,
                                max_depth=3
                            )
                            
                            if path:
                                context_items.append({
                                    "type": "path",
                                    "path": path.dict(),
                                    "text": self._format_path_for_rag(path),
                                    "relevance": 1.0,
                                    "source": "graph_path"
                                })
                
                elif strategy == "neighborhood":
                    # Extract neighborhood of each relevant node
                    for node_id in relevant_nodes:
                        subgraph = await self.extract_subgraph(
                            center_node_id=node_id,
                            max_depth=2,
                            max_nodes=10
                        )
                        
                        if subgraph:
                            context_items.append({
                                "type": "subgraph",
                                "subgraph": subgraph.dict(),
                                "text": self._format_subgraph_for_rag(subgraph),
                                "relevance": 1.0,
                                "source": "graph_neighborhood"
                            })
                
                else:  # hybrid
                    # Combine both approaches
                    # First get some paths
                    if len(relevant_nodes) >= 2:
                        path = await self.find_shortest_path(
                            start_node_id=relevant_nodes[0],
                            end_node_id=relevant_nodes[1],
                            max_depth=3
                        )
                        
                        if path:
                            context_items.append({
                                "type": "path",
                                "path": path.dict(),
                                "text": self._format_path_for_rag(path),
                                "relevance": 1.0,
                                "source": "graph_path"
                            })
                    
                    # Then get some neighborhoods
                    for node_id in relevant_nodes[:2]:
                        subgraph = await self.extract_subgraph(
                            center_node_id=node_id,
                            max_depth=1,
                            max_nodes=5
                        )
                        
                        if subgraph:
                            context_items.append({
                                "type": "subgraph",
                                "subgraph": subgraph.dict(),
                                "text": self._format_subgraph_for_rag(subgraph),
                                "relevance": 0.9,
                                "source": "graph_neighborhood"
                            })
            
            # If we have query embedding, use it to find semantically similar nodes
            elif query_embedding:
                async with self.pool.acquire() as conn:
                    # Load AGE extension
                    await conn.execute(f"LOAD '{self.config.age_schema}';")
                    
                    # Set graph
                    await conn.execute(f"SET graph_path = {self.config.graph_name};")
                    
                    # Find nodes with similar embeddings
                    # This assumes nodes have an 'embedding' property
                    embedding_str = f"[{','.join(map(str, query_embedding))}]"
                    
                    cypher = f"""
                        MATCH (n)
                        WHERE n.embedding IS NOT NULL
                        WITH n, n.embedding <-> ${embedding_str} AS distance
                        ORDER BY distance
                        LIMIT {max_results}
                        RETURN n
                    """
                    
                    result = await conn.fetch(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (node agtype);", 
                                           cypher, {}, True)
                    
                    # Process results
                    relevant_node_ids = []
                    for row in result:
                        node = json.loads(row['node'])
                        relevant_node_ids.append(node.get('id'))
                        
                        # Add node as context
                        context_items.append({
                            "type": "node",
                            "node": node,
                            "text": self._format_node_for_rag(node),
                            "relevance": 0.8,
                            "source": "graph_semantic_search"
                        })
                    
                    # If we found relevant nodes, extract a subgraph
                    if len(relevant_node_ids) > 0:
                        start_id = relevant_node_ids[0]
                        
                        # Get neighborhood of most relevant node
                        subgraph = await self.extract_subgraph(
                            center_node_id=start_id,
                            max_depth=2,
                            max_nodes=10
                        )
                        
                        if subgraph:
                            context_items.append({
                                "type": "subgraph",
                                "subgraph": subgraph.dict(),
                                "text": self._format_subgraph_for_rag(subgraph),
                                "relevance": 0.7,
                                "source": "graph_neighborhood"
                            })
            
            # If we only have query text, use it to search node properties
            else:
                async with self.pool.acquire() as conn:
                    # Load AGE extension
                    await conn.execute(f"LOAD '{self.config.age_schema}';")
                    
                    # Set graph
                    await conn.execute(f"SET graph_path = {self.config.graph_name};")
                    
                    # Find nodes with matching text
                    # This assumes nodes have properties like 'name', 'description', etc.
                    search_terms = query.split()
                    search_conditions = []
                    
                    for term in search_terms:
                        # Search in common properties
                        search_conditions.append(f"n.name =~ '(?i).*{term}.*'")
                        search_conditions.append(f"n.description =~ '(?i).*{term}.*'")
                        search_conditions.append(f"n.content =~ '(?i).*{term}.*'")
                    
                    cypher = f"""
                        MATCH (n)
                        WHERE {' OR '.join(search_conditions)}
                        RETURN n
                        LIMIT {max_results}
                    """
                    
                    result = await conn.fetch(f"SELECT * FROM cypher('{self.config.graph_name}', $1, $2, $3) as (node agtype);", 
                                           cypher, {}, True)
                    
                    # Process results
                    relevant_node_ids = []
                    for row in result:
                        node = json.loads(row['node'])
                        relevant_node_ids.append(node.get('id'))
                        
                        # Add node as context
                        context_items.append({
                            "type": "node",
                            "node": node,
                            "text": self._format_node_for_rag(node),
                            "relevance": 0.6,
                            "source": "graph_text_search"
                        })
            
            # Limit results
            if len(context_items) > max_results:
                # Sort by relevance
                context_items.sort(key=lambda x: x.get("relevance", 0), reverse=True)
                context_items = context_items[:max_results]
            
            return context_items
        
        except Exception as e:
            self.logger.error(f"Failed to find context for RAG: {e}")
            return []
    
    def _extract_path_elements(self, path_data):
        """Extract nodes and relationships from a path."""
        nodes = []
        relationships = []
        
        if isinstance(path_data, dict):
            # Handle result from single path query
            if 'vertices' in path_data:
                nodes = path_data.get('vertices', [])
            if 'edges' in path_data:
                relationships = path_data.get('edges', [])
        elif isinstance(path_data, list):
            # Handle result from path collection
            for item in path_data:
                if isinstance(item, dict):
                    if item.get('type') == 'node':
                        nodes.append(item)
                    elif item.get('type') == 'relationship':
                        relationships.append(item)
        
        return nodes, relationships
    
    def _generate_path_explanation(self, nodes, relationships, reasoning_type):
        """Generate an explanation for a path based on reasoning type."""
        if not nodes or not relationships:
            return "No path found."
        
        if reasoning_type == "causal":
            explanation = "This path represents a causal chain of events:\n"
            for i, rel in enumerate(relationships):
                start_node = nodes[i]
                end_node = nodes[i + 1]
                explanation += f"- {start_node.get('properties', {}).get('name', start_node.get('id'))} " + \
                               f"{rel.get('label')} " + \
                               f"{end_node.get('properties', {}).get('name', end_node.get('id'))}\n"
        
        elif reasoning_type == "hierarchical":
            explanation = "This path represents a hierarchical relationship:\n"
            for i, rel in enumerate(relationships):
                start_node = nodes[i]
                end_node = nodes[i + 1]
                explanation += f"- {start_node.get('properties', {}).get('name', start_node.get('id'))} " + \
                               f"{rel.get('label')} " + \
                               f"{end_node.get('properties', {}).get('name', end_node.get('id'))}\n"
        
        elif reasoning_type == "temporal":
            explanation = "This path represents a temporal sequence:\n"
            for i, rel in enumerate(relationships):
                start_node = nodes[i]
                end_node = nodes[i + 1]
                explanation += f"- {start_node.get('properties', {}).get('name', start_node.get('id'))} " + \
                               f"{rel.get('label')} " + \
                               f"{end_node.get('properties', {}).get('name', end_node.get('id'))}\n"
        
        else:
            explanation = "Path explanation:\n"
            for i, rel in enumerate(relationships):
                start_node = nodes[i]
                end_node = nodes[i + 1]
                explanation += f"- {start_node.get('properties', {}).get('name', start_node.get('id'))} " + \
                               f"{rel.get('label')} " + \
                               f"{end_node.get('properties', {}).get('name', end_node.get('id'))}\n"
        
        return explanation
    
    def _format_node_for_rag(self, node):
        """Format a node for RAG context."""
        props = node.get('properties', {})
        name = props.get('name', node.get('id', 'Unknown'))
        labels = ", ".join(node.get('labels', []))
        
        text = f"Node: {name} (Type: {labels})\n"
        
        # Add important properties
        for prop, value in props.items():
            if prop not in ['embedding', 'id', 'created_at']:
                text += f"- {prop}: {value}\n"
        
        return text
    
    def _format_path_for_rag(self, path):
        """Format a path for RAG context."""
        nodes = path.nodes
        relationships = path.relationships
        
        if not nodes or len(nodes) < 2:
            return "No valid path."
        
        text = f"Path from {nodes[0].get('properties', {}).get('name', nodes[0].get('id'))} " + \
               f"to {nodes[-1].get('properties', {}).get('name', nodes[-1].get('id'))}:\n"
        
        for i, rel in enumerate(relationships):
            start_node = nodes[i]
            end_node = nodes[i + 1]
            
            start_name = start_node.get('properties', {}).get('name', start_node.get('id'))
            end_name = end_node.get('properties', {}).get('name', end_node.get('id'))
            rel_type = rel.get('label', 'related to')
            
            text += f"- {start_name} {rel_type} {end_name}\n"
        
        return text
    
    def _format_subgraph_for_rag(self, subgraph):
        """Format a subgraph for RAG context."""
        center_node = subgraph.center_node
        nodes = subgraph.nodes
        relationships = subgraph.relationships
        
        center_name = center_node.get('properties', {}).get('name', center_node.get('id'))
        
        text = f"Knowledge graph centered on {center_name}:\n\n"
        
        # Add center node details
        text += f"Focus Entity: {center_name}\n"
        for prop, value in center_node.get('properties', {}).items():
            if prop not in ['embedding', 'id', 'created_at']:
                text += f"- {prop}: {value}\n"
        
        text += "\nRelated Information:\n"
        
        # Create a map of node IDs to nodes
        node_map = {node.get('id'): node for node in nodes}
        
        # Add relationship information
        for rel in relationships:
            if rel.get('start_id') == center_node.get('id'):
                # Outgoing relationship
                end_node = node_map.get(rel.get('end_id'))
                if end_node:
                    end_name = end_node.get('properties', {}).get('name', end_node.get('id'))
                    rel_type = rel.get('label', 'related to')
                    text += f"- {center_name} {rel_type} {end_name}\n"
            
            elif rel.get('end_id') == center_node.get('id'):
                # Incoming relationship
                start_node = node_map.get(rel.get('start_id'))
                if start_node:
                    start_name = start_node.get('properties', {}).get('name', start_node.get('id'))
                    rel_type = rel.get('label', 'related to')
                    text += f"- {start_name} {rel_type} {center_name}\n"
        
        return text
    
    # Cypher query builders for different algorithms
    
    def _build_shortest_path_query(self, start_id, end_id, rel_types, max_depth, node_filter, path_constraint):
        """Build Cypher query for shortest path."""
        # Construct relationship pattern
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        # Construct node filter
        node_where = []
        if node_filter:
            if node_filter.labels:
                node_labels = '|'.join(node_filter.labels)
                node_where.append(f"ALL(label IN LABELS(node) WHERE label IN ['{node_labels}'])")
            
            if node_filter.exclude_labels:
                exclude_labels = '|'.join(node_filter.exclude_labels)
                node_where.append(f"NONE(label IN LABELS(node) WHERE label IN ['{exclude_labels}'])")
            
            for prop, value in node_filter.properties.items():
                node_where.append(f"node.{prop} = '{value}'")
            
            for prop, value in node_filter.exclude_properties.items():
                node_where.append(f"node.{prop} <> '{value}'")
            
            if node_filter.min_degree:
                node_where.append(f"SIZE((node)--()) >= {node_filter.min_degree}")
            
            if node_filter.max_degree:
                node_where.append(f"SIZE((node)--()) <= {node_filter.max_degree}")
        
        node_where_clause = f"WHERE {' AND '.join(node_where)}" if node_where else ""
        
        # Construct path constraint
        path_where = []
        if path_constraint:
            if path_constraint.min_length:
                path_where.append(f"LENGTH(path) >= {path_constraint.min_length}")
            
            if path_constraint.max_length:
                path_where.append(f"LENGTH(path) <= {path_constraint.max_length}")
            
            if path_constraint.required_nodes:
                req_nodes = ', '.join([f"'{node}'" for node in path_constraint.required_nodes])
                path_where.append(f"ALL(node IN [{req_nodes}] WHERE node IN NODES(path))")
            
            if path_constraint.excluded_nodes:
                excl_nodes = ', '.join([f"'{node}'" for node in path_constraint.excluded_nodes])
                path_where.append(f"NONE(node IN [{excl_nodes}] WHERE node IN NODES(path))")
            
            if path_constraint.required_relationships:
                req_rels = ', '.join([f"'{rel}'" for rel in path_constraint.required_relationships])
                path_where.append(f"ANY(rel IN RELATIONSHIPS(path) WHERE TYPE(rel) IN [{req_rels}])")
            
            if path_constraint.excluded_relationships:
                excl_rels = ', '.join([f"'{rel}'" for rel in path_constraint.excluded_relationships])
                path_where.append(f"NONE(rel IN RELATIONSHIPS(path) WHERE TYPE(rel) IN [{excl_rels}])")
        
        path_where_clause = f"WHERE {' AND '.join(path_where)}" if path_where else ""
        
        # Build full query
        cypher = f"""
            MATCH path = shortestPath((a)-[r{rel_pattern}*1..{max_depth}]->(b))
            WHERE id(a) = '{start_id}' AND id(b) = '{end_id}'
            {path_where_clause}
            RETURN path
        """
        
        return cypher
    
    def _build_dijkstra_query(self, start_id, end_id, rel_types, max_depth, node_filter, path_constraint):
        """Build Cypher query for Dijkstra's algorithm."""
        # Implementation would use AGE's shortestPath function with property weights
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        # In this case, we assume relationships have a 'weight' property
        cypher = f"""
            MATCH path = shortestPath((a)-[r{rel_pattern}*1..{max_depth}]->(b))
            WHERE id(a) = '{start_id}' AND id(b) = '{end_id}'
            WITH path, REDUCE(weight = 0, r IN relationships(path) | weight + r.weight) AS totalWeight
            ORDER BY totalWeight ASC
            LIMIT 1
            RETURN path
        """
        
        return cypher
    
    def _build_a_star_query(self, start_id, end_id, rel_types, max_depth, node_filter, path_constraint):
        """Build Cypher query for A* algorithm."""
        # Note: Full A* requires heuristic functions that AGE might not support natively
        # This is a simplification using weights and distance
        
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        # We assume nodes have coordinates for distance calculation
        cypher = f"""
            MATCH path = (a)-[r{rel_pattern}*1..{max_depth}]->(b)
            WHERE id(a) = '{start_id}' AND id(b) = '{end_id}'
            WITH path, 
                 REDUCE(weight = 0, r IN relationships(path) | weight + r.weight) AS pathCost,
                 SQRT(POW(b.x - a.x, 2) + POW(b.y - a.y, 2)) AS heuristic
            ORDER BY pathCost + heuristic ASC
            LIMIT 1
            RETURN path
        """
        
        return cypher
    
    def _build_bidirectional_query(self, start_id, end_id, rel_types, max_depth, node_filter, path_constraint):
        """Build Cypher query for bidirectional search."""
        # Note: AGE might not support true bidirectional search natively
        # This is a simplification using two directions with an intersection
        
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        half_depth = max(1, max_depth // 2)
        
        cypher = f"""
            MATCH path1 = (a)-[r1{rel_pattern}*1..{half_depth}]->(meeting_node)
            WHERE id(a) = '{start_id}'
            MATCH path2 = (meeting_node)-[r2{rel_pattern}*1..{half_depth}]->(b)
            WHERE id(b) = '{end_id}'
            WITH path1, path2
            RETURN path1 + path2 AS path
            LIMIT 1
        """
        
        return cypher
    
    def _build_all_paths_query(self, start_id, end_id, rel_types, max_depth, max_paths, node_filter, path_constraint):
        """Build Cypher query for all paths."""
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        # Build full query
        cypher = f"""
            MATCH path = (a)-[r{rel_pattern}*1..{max_depth}]->(b)
            WHERE id(a) = '{start_id}' AND id(b) = '{end_id}'
            RETURN path
            LIMIT {max_paths}
        """
        
        return cypher
    
    def _build_neighborhood_query(self, center_id, max_depth, rel_types, node_filter, max_nodes):
        """Build Cypher query for neighborhood exploration."""
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        # Node filter clause
        node_where = []
        if node_filter:
            if node_filter.labels:
                node_labels = '|'.join(node_filter.labels)
                node_where.append(f"ANY(label IN LABELS(b) WHERE label IN ['{node_labels}'])")
            
            if node_filter.exclude_labels:
                exclude_labels = '|'.join(node_filter.exclude_labels)
                node_where.append(f"NONE(label IN LABELS(b) WHERE label IN ['{exclude_labels}'])")
            
            for prop, value in node_filter.properties.items():
                node_where.append(f"b.{prop} = '{value}'")
        
        node_where_clause = f"AND {' AND '.join(node_where)}" if node_where else ""
        
        # Build full query
        cypher = f"""
            MATCH path = (a)-[r{rel_pattern}*1..{max_depth}]-(b)
            WHERE id(a) = '{center_id}' 
            {node_where_clause}
            RETURN {{
                nodes: COLLECT(DISTINCT NODES(path)),
                relationships: COLLECT(DISTINCT RELATIONSHIPS(path))
            }} AS subgraph
            LIMIT {max_nodes}
        """
        
        return cypher
    
    def _build_pagerank_subgraph_query(self, center_id, max_depth, rel_types, node_filter, max_nodes):
        """Build Cypher query for PageRank-based subgraph extraction."""
        # Note: This is a simplification as AGE might not support PageRank natively
        # In a real implementation, you might need to implement PageRank separately
        
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        cypher = f"""
            MATCH path = (a)-[r{rel_pattern}*1..{max_depth}]-(b)
            WHERE id(a) = '{center_id}'
            WITH COLLECT(DISTINCT NODES(path)) AS nodes, COLLECT(DISTINCT RELATIONSHIPS(path)) AS rels
            RETURN {{
                nodes: nodes,
                relationships: rels
            }} AS subgraph
            LIMIT 1
        """
        
        return cypher
    
    def _build_common_neighbors_query(self, node_id, top_k, min_similarity, rel_types, node_filter):
        """Build Cypher query for common neighbors similarity."""
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        # Node filter clause
        node_where = []
        if node_filter:
            if node_filter.labels:
                node_labels = '|'.join(node_filter.labels)
                node_where.append(f"ANY(label IN LABELS(b) WHERE label IN ['{node_labels}'])")
            
            if node_filter.exclude_labels:
                exclude_labels = '|'.join(node_filter.exclude_labels)
                node_where.append(f"NONE(label IN LABELS(b) WHERE label IN ['{exclude_labels}'])")
        
        node_where_clause = f"AND {' AND '.join(node_where)}" if node_where else ""
        
        cypher = f"""
            MATCH (a)-[r1{rel_pattern}]-(common)-[r2{rel_pattern}]-(b)
            WHERE id(a) = '{node_id}' AND a <> b
            {node_where_clause}
            WITH a, b, COUNT(common) AS commonNeighbors
            WHERE commonNeighbors >= {min_similarity}
            RETURN b AS node, commonNeighbors AS similarity
            ORDER BY commonNeighbors DESC
            LIMIT {top_k}
        """
        
        return cypher
    
    def _build_jaccard_similarity_query(self, node_id, top_k, min_similarity, rel_types, node_filter):
        """Build Cypher query for Jaccard similarity."""
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        cypher = f"""
            MATCH (a)-[r1{rel_pattern}]-(common)-[r2{rel_pattern}]-(b)
            WHERE id(a) = '{node_id}' AND a <> b
            WITH a, b, COUNT(common) AS commonNeighbors
            MATCH (a)-[r3{rel_pattern}]-(aNeighbor)
            WITH a, b, commonNeighbors, COLLECT(aNeighbor) AS aNeighbors
            MATCH (b)-[r4{rel_pattern}]-(bNeighbor)
            WITH a, b, commonNeighbors, aNeighbors, COLLECT(bNeighbor) AS bNeighbors
            WITH a, b, commonNeighbors, SIZE(aNeighbors) + SIZE(bNeighbors) - commonNeighbors AS totalNeighbors
            WITH a, b, commonNeighbors, totalNeighbors, 1.0 * commonNeighbors / totalNeighbors AS jaccard
            WHERE jaccard >= {min_similarity}
            RETURN b AS node, jaccard AS similarity
            ORDER BY jaccard DESC
            LIMIT {top_k}
        """
        
        return cypher
    
    def _build_adamic_adar_query(self, node_id, top_k, min_similarity, rel_types, node_filter):
        """Build Cypher query for Adamic-Adar similarity."""
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        cypher = f"""
            MATCH (a)-[r1{rel_pattern}]-(common)-[r2{rel_pattern}]-(b)
            WHERE id(a) = '{node_id}' AND a <> b
            WITH a, b, common
            MATCH (common)-[r3{rel_pattern}]-(neighbor)
            WITH a, b, common, COUNT(neighbor) AS commonDegree
            WITH a, b, SUM(1.0 / LOG(commonDegree + 0.1)) AS adamicAdar
            WHERE adamicAdar >= {min_similarity}
            RETURN b AS node, adamicAdar AS similarity
            ORDER BY adamicAdar DESC
            LIMIT {top_k}
        """
        
        return cypher
    
    def _build_causal_reasoning_query(self, start_id, end_id, max_depth, rel_types):
        """Build Cypher query for causal reasoning."""
        # Causal relationships typically represent "cause and effect"
        # so we want to find paths that maintain causal direction
        
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        cypher = f"""
            MATCH path = (a)-[r{rel_pattern}*1..{max_depth}]->(b)
            WHERE id(a) = '{start_id}' AND id(b) = '{end_id}'
            RETURN path
            LIMIT 1
        """
        
        return cypher
    
    def _build_hierarchical_reasoning_query(self, start_id, end_id, max_depth, rel_types):
        """Build Cypher query for hierarchical reasoning."""
        # Hierarchical reasoning might involve both upward and downward traversal
        
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        cypher = f"""
            MATCH path = (a)-[r{rel_pattern}*1..{max_depth}]-(b)
            WHERE id(a) = '{start_id}' AND id(b) = '{end_id}'
            RETURN path
            LIMIT 1
        """
        
        return cypher
    
    def _build_temporal_reasoning_query(self, start_id, end_id, max_depth, rel_types):
        """Build Cypher query for temporal reasoning."""
        # Temporal reasoning often involves directed relationships with time constraints
        
        rel_pattern = ""
        if rel_types and len(rel_types) > 0:
            rel_types_str = '|'.join(rel_types)
            rel_pattern = f":{rel_types_str}"
        
        cypher = f"""
            MATCH path = (a)-[r{rel_pattern}*1..{max_depth}]->(b)
            WHERE id(a) = '{start_id}' AND id(b) = '{end_id}'
            WITH path
            UNWIND relationships(path) AS rel
            WITH path, COLLECT(rel.timestamp) AS timestamps
            WHERE ALL(i IN RANGE(0, SIZE(timestamps) - 2) WHERE timestamps[i] <= timestamps[i+1])
            RETURN path
            LIMIT 1
        """
        
        return cypher
    
    def _build_louvain_community_query(self, min_community_size, max_communities):
        """Build Cypher query for Louvain community detection."""
        # Note: AGE might not have built-in Louvain algorithm
        # This is a simplified representation
        
        cypher = f"""
            MATCH (n)-[r]-(m)
            WITH COLLECT(n) AS nodes, COLLECT(r) AS rels
            CALL apoc.algo.louvain(nodes, rels) YIELD communities
            UNWIND communities AS community
            WITH community
            WHERE SIZE(community) >= {min_community_size}
            RETURN community
            LIMIT {max_communities}
        """
        
        # In practice, you might need a custom implementation or use a different approach
        return cypher
    
    def _build_label_propagation_query(self, min_community_size, max_communities):
        """Build Cypher query for label propagation community detection."""
        # Note: AGE might not have built-in label propagation
        # This is a simplified representation
        
        cypher = f"""
            MATCH (n)-[r]-(m)
            WITH COLLECT(n) AS nodes, COLLECT(r) AS rels
            CALL apoc.algo.labelPropagation(nodes, rels) YIELD communities
            UNWIND communities AS community
            WITH community
            WHERE SIZE(community) >= {min_community_size}
            RETURN community
            LIMIT {max_communities}
        """
        
        # In practice, you might need a custom implementation
        return cypher


# Factory function for graph navigators
async def create_graph_navigator(
    connection_string: str,
    graph_name: str = "knowledge_graph",
    logger: Optional[logging.Logger] = None
) -> GraphNavigator:
    """
    Create a graph navigator instance.
    
    Args:
        connection_string: Database connection string
        graph_name: Name of the graph
        logger: Optional logger
        
    Returns:
        Initialized graph navigator
    """
    config = GraphNavigatorConfig(
        graph_name=graph_name,
        default_max_depth=3,
        default_max_results=10,
        cache_results=True
    )
    
    navigator = GraphNavigator(connection_string, config, logger=logger)
    await navigator.initialize()
    
    return navigator