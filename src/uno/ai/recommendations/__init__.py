"""
Recommendation engine system for the Uno framework.

This module provides recommendation capabilities to suggest relevant
items to users based on their preferences and behaviors.
"""

from uno.ai.recommendations.engine import RecommendationEngine
from uno.ai.recommendations.api import create_recommendation_router

__all__ = ["RecommendationEngine", "create_recommendation_router"]