# Middleware Optimization Plan

## Overview

API middleware components add measurable overhead to request processing in the Uno framework. This document outlines the approach for optimizing middleware processing to reduce latency and resource consumption while maintaining functionality.

## Key Optimization Areas

### 1. Middleware Pipeline Refactoring

Refactor the middleware pipeline for early short-circuiting and conditional execution:

- **Prioritized Execution**: Ensure critical middleware runs first
- **Early Termination**: Add short-circuit mechanisms for common cases
- **Conditional Execution**: Skip unnecessary middleware based on request characteristics
- **Pipeline Compression**: Combine compatible middleware components

Implementation strategy:
```python
class OptimizedMiddlewarePipeline:
    """
    Optimized middleware pipeline with early termination and conditional execution.
    """
    
    def __init__(self):
        self.middleware_groups = {
            "critical": [],      # Authentication, security (always run first)
            "pre_processing": [], # Request transformation, validation
            "business_logic": [], # Application-specific middleware
            "post_processing": [], # Response transformation
            "monitoring": []     # Metrics, logging (always run, but can be deferred)
        }
        self.conditional_rules = {}
        self.skip_patterns = {}
        
    def add_middleware(self, middleware, group="business_logic", 
                       condition=None, skip_pattern=None):
        """Add middleware to the appropriate group with optional conditions."""
        self.middleware_groups[group].append(middleware)
        
        if condition:
            self.conditional_rules[id(middleware)] = condition
            
        if skip_pattern:
            self.skip_patterns[id(middleware)] = skip_pattern
    
    async def process_request(self, request):
        """Process a request through the optimized middleware pipeline."""
        response = None
        context = {"short_circuit": False}
        
        # Process middleware in order of groups
        for group in ["critical", "pre_processing", "business_logic", 
                      "post_processing", "monitoring"]:
            
            if context.get("short_circuit") and group not in ["critical", "monitoring"]:
                continue
                
            for middleware in self.middleware_groups[group]:
                # Check skip conditions
                should_skip = False
                
                # Skip based on explicit patterns
                if id(middleware) in self.skip_patterns:
                    pattern = self.skip_patterns[id(middleware)]
                    if pattern.match(request):
                        should_skip = True
                
                # Skip based on conditional rules
                if id(middleware) in self.conditional_rules and not should_skip:
                    condition_func = self.conditional_rules[id(middleware)]
                    should_run = await condition_func(request, context)
                    should_skip = not should_run
                
                if should_skip:
                    continue
                
                # Process middleware
                try:
                    if response is None:
                        response = await middleware.process_request(request, context)
                    else:
                        response = await middleware.process_response(request, response, context)
                    
                    # Check for short-circuit
                    if context.get("short_circuit"):
                        break
                        
                except Exception as e:
                    # Handle errors appropriately - might short-circuit
                    context["short_circuit"] = True
                    context["error"] = e
                    response = create_error_response(e)
                    break
        
        return response
```

### 2. Middleware Result Caching

Implement caching for middleware results:

- **Cross-Request Caching**: Cache middleware results across similar requests
- **In-Request Caching**: Cache intermediate results within a single request
- **Hierarchical Invalidation**: Create hierarchical cache invalidation for middleware
- **Minimal Recomputation**: Only recompute affected middleware results on changes

Implementation strategy:
```python
class CachedMiddlewareResult:
    """Cache container for middleware results."""
    
    def __init__(self, result, metadata=None, dependencies=None):
        self.result = result
        self.created_at = time.time()
        self.metadata = metadata or {}
        self.dependencies = dependencies or set()
        self.hit_count = 0
    
    def is_valid(self, ttl=60.0):
        """Check if the cached result is still valid."""
        age = time.time() - self.created_at
        return age < ttl
        
    def record_hit(self):
        """Record a cache hit."""
        self.hit_count += 1

class MiddlewareCacheManager:
    """Manager for middleware result caching."""
    
    def __init__(self):
        self.cache = {}
        self.dependency_graph = defaultdict(set)
        self.stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0
        }
        self._lock = asyncio.Lock()
    
    async def get(self, middleware_id, request_hash, ttl=60.0):
        """Get a cached middleware result."""
        cache_key = f"{middleware_id}:{request_hash}"
        
        async with self._lock:
            if cache_key in self.cache and self.cache[cache_key].is_valid(ttl):
                self.cache[cache_key].record_hit()
                self.stats["hits"] += 1
                return self.cache[cache_key].result
                
        self.stats["misses"] += 1
        return None
    
    async def set(self, middleware_id, request_hash, result, 
                 metadata=None, dependencies=None):
        """Set a cached middleware result."""
        cache_key = f"{middleware_id}:{request_hash}"
        
        async with self._lock:
            self.cache[cache_key] = CachedMiddlewareResult(
                result, metadata, dependencies
            )
            
            # Update dependency graph
            if dependencies:
                for dep in dependencies:
                    self.dependency_graph[dep].add(cache_key)
    
    async def invalidate(self, dependency_key):
        """Invalidate cache entries based on a dependency key."""
        async with self._lock:
            # Find all cache keys that depend on this key
            affected_keys = self.dependency_graph.get(dependency_key, set())
            
            # Invalidate affected keys
            for key in affected_keys:
                if key in self.cache:
                    del self.cache[key]
                    self.stats["invalidations"] += 1
            
            # Recursively invalidate dependencies of dependencies
            for key in affected_keys:
                await self.invalidate(key)
                
            # Clean up dependency graph
            if dependency_key in self.dependency_graph:
                del self.dependency_graph[dependency_key]
```

### 3. Lazy Middleware Execution

Implement lazy/deferred execution for non-critical middleware:

- **Deferred Processing**: Defer non-critical middleware execution
- **Prioritized Computation**: Process middleware based on priority and dependencies
- **Background Processing**: Move applicable middleware to background tasks
- **Incremental Rendering**: Support incremental response rendering with deferred middleware

Implementation strategy:
```python
class LazyMiddlewareExecutor:
    """Executor for lazy middleware processing."""
    
    def __init__(self, response_sender):
        self.response_sender = response_sender
        self.background_tasks = []
        self.deferred_middleware = []
        self.critical_results = {}
    
    def add_critical_middleware(self, middleware, request):
        """Add critical middleware that must be executed before response."""
        self.deferred_middleware.append((middleware, request, True))
    
    def add_deferred_middleware(self, middleware, request):
        """Add middleware that can be deferred until after initial response."""
        self.deferred_middleware.append((middleware, request, False))
    
    def add_background_task(self, task_func, *args, **kwargs):
        """Add a background task to run after response is sent."""
        self.background_tasks.append((task_func, args, kwargs))
    
    async def execute_critical_middleware(self):
        """Execute all critical middleware and return initial results."""
        results = {}
        
        for middleware, request, is_critical in self.deferred_middleware:
            if is_critical:
                result = await middleware.process_request(request)
                results[id(middleware)] = result
        
        self.critical_results = results
        return results
    
    async def send_initial_response(self, response):
        """Send initial response with critical middleware results."""
        await self.response_sender.send_response(response)
    
    async def process_deferred_middleware(self):
        """Process deferred middleware and send updates if needed."""
        for middleware, request, is_critical in self.deferred_middleware:
            if not is_critical:
                try:
                    result = await middleware.process_request(request)
                    
                    # If middleware produces supplementary data, send it
                    if hasattr(middleware, 'produces_supplements') and middleware.produces_supplements:
                        await self.response_sender.send_supplement(result)
                except Exception as e:
                    # Log but don't fail the response
                    logger.error(f"Error in deferred middleware {middleware}: {e}")
    
    async def execute_background_tasks(self):
        """Execute background tasks."""
        for task_func, args, kwargs in self.background_tasks:
            try:
                asyncio.create_task(task_func(*args, **kwargs))
            except Exception as e:
                logger.error(f"Error scheduling background task {task_func}: {e}")
    
    async def execute_all(self, initial_response):
        """Execute all middleware and tasks in appropriate order."""
        # Process critical middleware
        await self.execute_critical_middleware()
        
        # Send initial response
        await self.send_initial_response(initial_response)
        
        # Process deferred middleware
        await self.process_deferred_middleware()
        
        # Execute background tasks
        await self.execute_background_tasks()
```

### 4. Optimized Core Middleware Components

Optimize the core middleware components:

- **Authentication Optimization**: Optimize token validation and user lookup
- **Error Handling Enhancement**: Streamline error handling middleware
- **Request Parsing Improvements**: Optimize request parsing middleware
- **Response Formatting Optimization**: Enhance response formatting efficiency

Implementation approach for authentication middleware:
```python
class OptimizedAuthMiddleware:
    """Optimized authentication middleware with caching and early returns."""
    
    def __init__(self, auth_service, cache_ttl=300):
        self.auth_service = auth_service
        self.token_cache = TTLCache(maxsize=10000, ttl=cache_ttl)
        self.user_cache = TTLCache(maxsize=5000, ttl=cache_ttl)
        self.exempt_routes = set()
        self.public_routes = set()
    
    def exempt_route(self, route_pattern):
        """Mark a route as exempt from authentication."""
        self.exempt_routes.add(route_pattern)
    
    def mark_public_route(self, route_pattern):
        """Mark a route as public (allows anonymous access)."""
        self.public_routes.add(route_pattern)
    
    def _is_route_exempt(self, path):
        """Check if route is exempt from authentication."""
        return any(re.match(pattern, path) for pattern in self.exempt_routes)
    
    def _is_route_public(self, path):
        """Check if route allows anonymous access."""
        return any(re.match(pattern, path) for pattern in self.public_routes)
    
    async def process_request(self, request, context=None):
        """Process the request with optimized authentication."""
        path = request.url.path
        
        # Early return for exempt routes
        if self._is_route_exempt(path):
            context["authenticated"] = False
            context["short_circuit_auth"] = True
            return request
        
        # Get token from request
        token = self._extract_token(request)
        
        if not token:
            # Handle missing token
            if self._is_route_public(path):
                # Anonymous access allowed
                context["authenticated"] = False
                return request
            else:
                # Authentication required
                context["short_circuit"] = True
                return JSONResponse(
                    status_code=401,
                    content={"error": "Authentication required"}
                )
        
        # Check token cache
        cached_user_id = self.token_cache.get(token)
        if cached_user_id:
            # Get user from cache
            user = self.user_cache.get(cached_user_id)
            if user:
                # Set user in context
                context["user"] = user
                context["authenticated"] = True
                return request
        
        # Validate token
        try:
            user_id = await self.auth_service.validate_token(token)
            if not user_id:
                context["short_circuit"] = True
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid authentication token"}
                )
            
            # Cache token -> user_id mapping
            self.token_cache[token] = user_id
            
            # Get user details
            user = await self.auth_service.get_user(user_id)
            if not user:
                context["short_circuit"] = True
                return JSONResponse(
                    status_code=401,
                    content={"error": "User not found"}
                )
            
            # Cache user
            self.user_cache[user_id] = user
            
            # Set user in context
            context["user"] = user
            context["authenticated"] = True
            return request
            
        except Exception as e:
            # Handle authentication errors
            context["short_circuit"] = True
            return JSONResponse(
                status_code=401,
                content={"error": f"Authentication error: {str(e)}"}
            )
    
    def _extract_token(self, request):
        """Extract authentication token from request with optimized checks."""
        # Check authorization header first (most common)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]
        
        # Check cookie
        token = request.cookies.get("auth_token")
        if token:
            return token
        
        # Check query params
        token = request.query_params.get("token")
        if token:
            return token
        
        return None
```

### 5. Middleware Composition and Reuse

Enhance middleware composition and reuse:

- **Middleware Factory**: Create middleware factory with reusable building blocks
- **Composable Middleware**: Enable functional composition of middleware
- **Stacked Middleware**: Support stacking middleware with optional interception
- **Specialized Middleware Chains**: Create optimized chains for common request types

Implementation approach:
```python
class MiddlewareComposer:
    """Composer for building efficient middleware chains."""
    
    @staticmethod
    def compose(*middleware_funcs):
        """Compose multiple middleware functions into a single middleware."""
        
        async def composed_middleware(request, call_next):
            # Build the middleware chain from inside out
            handler = call_next
            
            for middleware in reversed(middleware_funcs):
                prev_handler = handler
                
                # Create a closure to call the current middleware with the next handler
                async def create_handler(mw, next_handler):
                    async def handle(req):
                        return await mw(req, next_handler)
                    return handle
                
                handler = await create_handler(middleware, prev_handler)
            
            # Execute the outermost middleware with the request
            return await handler(request)
        
        return composed_middleware
    
    @staticmethod
    def conditional(condition_func, middleware):
        """Create a middleware that only runs if a condition is met."""
        
        async def conditional_middleware(request, call_next):
            if await condition_func(request):
                return await middleware(request, call_next)
            return await call_next(request)
        
        return conditional_middleware
    
    @staticmethod
    def cached(cache_key_func, ttl=60):
        """Create a middleware that caches responses."""
        cache = TTLCache(maxsize=1000, ttl=ttl)
        
        async def cached_middleware(request, call_next):
            # Generate cache key
            key = await cache_key_func(request)
            
            # Check cache
            if key in cache:
                return cache[key]
            
            # Execute middleware chain
            response = await call_next(request)
            
            # Cache response
            cache[key] = response
            return response
        
        return cached_middleware
    
    @staticmethod
    def timed(name):
        """Create a middleware that times execution."""
        
        async def timed_middleware(request, call_next):
            start_time = time.time()
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record timing
            metrics.record_middleware_timing(name, duration)
            return response
        
        return timed_middleware
    
    @staticmethod
    def create_chain(middlewares, base_app):
        """Create a middleware chain from a list of middlewares."""
        app = base_app
        
        for middleware in reversed(middlewares):
            app = middleware(app)
        
        return app
```

### 6. Middleware Profiling and Optimization Feedback

Add profiling and optimization feedback mechanisms:

- **Detailed Timing**: Implement detailed timing of middleware components
- **Hotspot Identification**: Automatically identify middleware bottlenecks
- **Optimization Suggestions**: Generate optimization suggestions based on profiling
- **Adaptive Middleware**: Create self-adjusting middleware based on usage patterns

Implementation approach:
```python
class MiddlewareProfiler:
    """Profiler for middleware performance analysis."""
    
    def __init__(self):
        self.timings = defaultdict(list)
        self.request_counts = defaultdict(int)
        self.bottlenecks = []
        self.last_analysis = 0
        self.analysis_interval = 3600  # 1 hour
    
    async def wrap_middleware(self, middleware_func, name):
        """Wrap middleware function with timing."""
        
        async def wrapped_middleware(request, call_next):
            start_time = time.time()
            
            try:
                response = await middleware_func(request, call_next)
                duration = time.time() - start_time
                
                # Record timing
                request_path = request.url.path
                self.timings[f"{name}:{request_path}"].append(duration)
                self.request_counts[request_path] += 1
                
                # Keep timings list manageable
                if len(self.timings[f"{name}:{request_path}"]) > 100:
                    self.timings[f"{name}:{request_path}"] = self.timings[f"{name}:{request_path}"][-100:]
                
                # Trigger analysis if needed
                await self._maybe_analyze()
                
                return response
            except Exception as e:
                # Record error and re-raise
                duration = time.time() - start_time
                self.timings[f"{name}:{request_path}_error"].append(duration)
                raise
        
        return wrapped_middleware
    
    async def _maybe_analyze(self):
        """Run analysis if it's time."""
        now = time.time()
        if now - self.last_analysis > self.analysis_interval:
            await self.analyze_performance()
            self.last_analysis = now
    
    async def analyze_performance(self):
        """Analyze middleware performance and identify bottlenecks."""
        self.bottlenecks = []
        
        # Group by middleware
        middleware_timings = defaultdict(list)
        
        for key, timings in self.timings.items():
            if not timings:
                continue
                
            middleware_name = key.split(":")[0]
            middleware_timings[middleware_name].extend(timings)
        
        # Calculate stats
        stats = {}
        
        for middleware, timings in middleware_timings.items():
            if not timings:
                continue
                
            avg = sum(timings) / len(timings)
            p95 = sorted(timings)[int(len(timings) * 0.95)]
            p99 = sorted(timings)[int(len(timings) * 0.99)]
            
            stats[middleware] = {
                "avg": avg,
                "p95": p95,
                "p99": p99,
                "count": len(timings)
            }
            
            # Identify bottlenecks
            if avg > 0.1:  # More than 100ms average
                self.bottlenecks.append({
                    "middleware": middleware,
                    "avg_time": avg,
                    "p95": p95,
                    "p99": p99,
                    "severity": "high" if avg > 0.5 else "medium"
                })
            elif p95 > 0.5:  # p95 > 500ms
                self.bottlenecks.append({
                    "middleware": middleware,
                    "avg_time": avg,
                    "p95": p95,
                    "p99": p99,
                    "severity": "medium"
                })
        
        # Return analysis results
        return {
            "stats": stats,
            "bottlenecks": self.bottlenecks,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self):
        """Generate optimization recommendations based on bottlenecks."""
        recommendations = []
        
        for bottleneck in self.bottlenecks:
            middleware = bottleneck["middleware"]
            severity = bottleneck["severity"]
            
            if severity == "high":
                recommendations.append({
                    "middleware": middleware,
                    "recommendation": "Consider caching results or moving to background processing",
                    "severity": "high"
                })
            elif severity == "medium":
                recommendations.append({
                    "middleware": middleware,
                    "recommendation": "Optimize internal logic or implement conditional execution",
                    "severity": "medium"
                })
        
        return recommendations
```

## Implementation Approach

### Phase 1: Core Refactoring

1. Refactor middleware pipeline for early termination
2. Implement conditional middleware execution
3. Optimize core middleware components (authentication, error handling)

### Phase 2: Caching and Optimizations

1. Implement middleware result caching
2. Add lazy/deferred middleware execution
3. Create specialized middleware chains for common request types

### Phase 3: Advanced Features

1. Implement middleware composition utilities
2. Add profiling and optimization feedback
3. Create adaptive middleware mechanisms

## Expected Improvements

| Metric | Expected Improvement |
|--------|----------------------|
| Middleware processing time | 30-50% reduction |
| API response latency | 15-30% reduction |
| Resource utilization | 20-40% improvement |
| Cache hit rate | 60-80% for common patterns |
| Peak throughput | 20-40% increase |

## Monitoring and Validation

To validate the effectiveness of these optimizations:

1. Compare middleware processing times before and after implementation
2. Measure API response latency under various load conditions
3. Track resource utilization during peak traffic
4. Monitor cache hit rates for middleware results
5. Record performance improvements by endpoint and middleware type

## Fallback Strategy

If any optimization causes unexpected issues:

1. Implement feature flags for each optimization category
2. Add circuit breakers for complex middleware patterns
3. Create graceful degradation paths for middleware chains
4. Support hybrid mode with optimized/standard middleware selection
5. Build comprehensive monitoring for early detection of problems