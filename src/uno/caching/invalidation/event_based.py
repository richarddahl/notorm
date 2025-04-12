"""Event-based cache invalidation module.

This module provides an event-based invalidation strategy.
"""

from typing import Any, Dict, List, Optional, Pattern, Set, Union
import re
import fnmatch
import threading
import asyncio


class EventBasedInvalidation:
    """Event-based cache invalidation strategy.
    
    This strategy invalidates cache entries based on events that are triggered
    by the application.
    """
    
    def __init__(self, event_handlers: Optional[Dict[str, List[str]]] = None):
        """Initialize the event-based invalidation strategy.
        
        Args:
            event_handlers: Optional mapping of event types to patterns to invalidate.
                          For example: {"user.updated": ["user:*", "profile:*"]}
        """
        self.event_handlers = event_handlers or {}
        self._pattern_cache: Dict[str, Pattern] = {}
        self._lock = threading.RLock()
        self._pending_invalidations: Set[str] = set()
    
    def invalidate(self, key: str, value: Any) -> bool:
        """Determine if a value should be invalidated based on events.
        
        This method always returns False because event-based invalidation is driven
        by events, not by cache lookups.
        
        Args:
            key: The cache key.
            value: The cached value.
            
        Returns:
            True if the value should be invalidated, False otherwise.
        """
        # Event-based invalidation is driven by events, not by cache lookups
        return False
    
    def handle_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> List[str]:
        """Handle an event and determine which patterns should be invalidated.
        
        Args:
            event_type: The type of the event.
            payload: Optional event payload with additional information.
            
        Returns:
            A list of patterns to invalidate.
        """
        patterns: List[str] = []
        
        # Add patterns for the exact event type
        if event_type in self.event_handlers:
            patterns.extend(self.event_handlers[event_type])
        
        # Add patterns for wildcard event types (using fnmatch)
        for event_pattern, handler_patterns in self.event_handlers.items():
            if "*" in event_pattern and fnmatch.fnmatch(event_type, event_pattern):
                patterns.extend(handler_patterns)
        
        # Add dynamic patterns based on the payload
        if payload and event_type in self.event_handlers:
            # Get handler patterns for this event type
            handler_patterns = self.event_handlers[event_type]
            
            # For each pattern that contains curly braces ({}), substitute values from the payload
            for pattern in handler_patterns:
                if "{" in pattern and "}" in pattern:
                    # Try to format the pattern with the payload
                    try:
                        formatted_pattern = pattern.format(**payload)
                        if formatted_pattern not in patterns:
                            patterns.append(formatted_pattern)
                    except KeyError:
                        # If formatting fails, still include the original pattern
                        if pattern not in patterns:
                            patterns.append(pattern)
        
        return patterns
    
    async def handle_event_async(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> List[str]:
        """Handle an event asynchronously and determine which patterns should be invalidated.
        
        This is the async version of the handle_event method.
        
        Args:
            event_type: The type of the event.
            payload: Optional event payload with additional information.
            
        Returns:
            A list of patterns to invalidate.
        """
        # Run the synchronous method in a thread to avoid blocking the event loop
        return await asyncio.to_thread(self.handle_event, event_type, payload)
    
    def register_event_handler(self, event_type: str, patterns: List[str]) -> None:
        """Register an event handler for a specific event type.
        
        Args:
            event_type: The type of the event.
            patterns: The patterns to invalidate when this event occurs.
        """
        with self._lock:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            
            # Add unique patterns
            for pattern in patterns:
                if pattern not in self.event_handlers[event_type]:
                    self.event_handlers[event_type].append(pattern)
    
    def unregister_event_handler(self, event_type: str, pattern: Optional[str] = None) -> None:
        """Unregister an event handler.
        
        Args:
            event_type: The type of the event.
            pattern: Optional pattern to unregister. If not provided, all patterns
                    for this event type will be unregistered.
        """
        with self._lock:
            if event_type not in self.event_handlers:
                return
            
            if pattern is None:
                # Unregister all patterns for this event type
                del self.event_handlers[event_type]
            else:
                # Unregister a specific pattern
                if pattern in self.event_handlers[event_type]:
                    self.event_handlers[event_type].remove(pattern)
                
                # If no patterns left, remove the event type
                if not self.event_handlers[event_type]:
                    del self.event_handlers[event_type]
    
    def match_pattern(self, key: str, pattern: str) -> bool:
        """Check if a key matches a pattern.
        
        Args:
            key: The cache key.
            pattern: The pattern to match against.
            
        Returns:
            True if the key matches the pattern, False otherwise.
        """
        # Try to use a cached regular expression for this pattern
        with self._lock:
            if pattern not in self._pattern_cache:
                # Convert the pattern to a regular expression
                if "*" in pattern or "?" in pattern or "[" in pattern:
                    # Pattern has wildcards, use fnmatch to convert to regex
                    regex_pattern = fnmatch.translate(pattern)
                else:
                    # Pattern is a literal string, match exactly
                    regex_pattern = f"^{re.escape(pattern)}$"
                
                # Compile the regular expression
                self._pattern_cache[pattern] = re.compile(regex_pattern)
            
            # Get the compiled pattern
            compiled_pattern = self._pattern_cache[pattern]
        
        # Match the key against the pattern
        return bool(compiled_pattern.match(key))
