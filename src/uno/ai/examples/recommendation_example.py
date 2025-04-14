"""
Example of using the recommendation engine in the Uno framework.

This module provides a complete example of how to use the recommendation
functionality, including integration with FastAPI and domain entities.
"""

import asyncio
import logging
import random
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field

from uno.ai.recommendations import RecommendationEngine, create_recommendation_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Uno Recommendation Example")

# Sample product entity
class Product(BaseModel):
    """Product entity for recommendations."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Sample user entity
class User(BaseModel):
    """User entity for recommendations."""
    
    id: UUID = Field(default_factory=uuid4)
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Sample interaction entity
class Interaction(BaseModel):
    """User-product interaction entity."""
    
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID = Field(..., description="User ID")
    product_id: UUID = Field(..., description="Product ID")
    interaction_type: str = Field(..., description="Interaction type")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Repositories
class ProductRepository:
    """Simple in-memory repository for products."""
    
    def __init__(self):
        """Initialize the repository."""
        self.products: Dict[UUID, Product] = {}
    
    async def get_by_id(self, id: UUID) -> Optional[Product]:
        """Get a product by ID."""
        return self.products.get(id)
    
    async def list(self) -> List[Product]:
        """List all products."""
        return list(self.products.values())
    
    async def create(self, product: Product) -> Product:
        """Create a new product."""
        self.products[product.id] = product
        return product


class UserRepository:
    """Simple in-memory repository for users."""
    
    def __init__(self):
        """Initialize the repository."""
        self.users: Dict[UUID, User] = {}
    
    async def get_by_id(self, id: UUID) -> Optional[User]:
        """Get a user by ID."""
        return self.users.get(id)
    
    async def list(self) -> List[User]:
        """List all users."""
        return list(self.users.values())
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        self.users[user.id] = user
        return user


class InteractionRepository:
    """Simple in-memory repository for interactions."""
    
    def __init__(self):
        """Initialize the repository."""
        self.interactions: Dict[UUID, Interaction] = {}
    
    async def list(self) -> List[Interaction]:
        """List all interactions."""
        return list(self.interactions.values())
    
    async def create(self, interaction: Interaction) -> Interaction:
        """Create a new interaction."""
        self.interactions[interaction.id] = interaction
        return interaction
    
    async def get_by_user(self, user_id: UUID) -> List[Interaction]:
        """Get all interactions for a user."""
        return [
            interaction for interaction in self.interactions.values()
            if interaction.user_id == user_id
        ]


# Create repositories
product_repository = ProductRepository()
user_repository = UserRepository()
interaction_repository = InteractionRepository()


# Dependencies
def get_product_repository():
    """Get the product repository."""
    return product_repository


def get_user_repository():
    """Get the user repository."""
    return user_repository


def get_interaction_repository():
    """Get the interaction repository."""
    return interaction_repository


# Create recommendation engine
async def setup_recommendation_engine():
    """Set up the recommendation engine."""
    # Create engine
    engine = RecommendationEngine()
    
    # Initialize engine
    await engine.initialize()
    
    return engine


# Request and response models
class ProductResponse(BaseModel):
    """Response model for products."""
    
    id: UUID
    name: str
    description: str
    price: float
    category: str


class UserResponse(BaseModel):
    """Response model for users."""
    
    id: UUID
    username: str
    email: str


class InteractionCreate(BaseModel):
    """Request model for creating an interaction."""
    
    user_id: UUID
    product_id: UUID
    interaction_type: str = Field(..., description="view, like, purchase, etc.")


class InteractionResponse(BaseModel):
    """Response model for interactions."""
    
    id: UUID
    user_id: UUID
    product_id: UUID
    interaction_type: str
    timestamp: datetime


class ProductRecommendation(BaseModel):
    """Model for a product recommendation."""
    
    id: UUID
    name: str
    description: str
    price: float
    category: str
    score: float


# Routers
product_router = APIRouter(prefix="/api/products", tags=["products"])
user_router = APIRouter(prefix="/api/users", tags=["users"])
interaction_router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@product_router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    name: str,
    description: str,
    price: float,
    category: str,
    repository: ProductRepository = Depends(get_product_repository)
):
    """Create a new product."""
    product = Product(
        name=name,
        description=description,
        price=price,
        category=category
    )
    return await repository.create(product)


@product_router.get("", response_model=List[ProductResponse])
async def list_products(
    repository: ProductRepository = Depends(get_product_repository)
):
    """List all products."""
    return await repository.list()


@product_router.get("/{id}", response_model=ProductResponse)
async def get_product(
    id: UUID,
    repository: ProductRepository = Depends(get_product_repository)
):
    """Get a product by ID."""
    product = await repository.get_by_id(id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@user_router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    username: str,
    email: str,
    repository: UserRepository = Depends(get_user_repository)
):
    """Create a new user."""
    user = User(
        username=username,
        email=email
    )
    return await repository.create(user)


@user_router.get("", response_model=List[UserResponse])
async def list_users(
    repository: UserRepository = Depends(get_user_repository)
):
    """List all users."""
    return await repository.list()


@user_router.get("/{id}", response_model=UserResponse)
async def get_user(
    id: UUID,
    repository: UserRepository = Depends(get_user_repository)
):
    """Get a user by ID."""
    user = await repository.get_by_id(id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@interaction_router.post("", response_model=InteractionResponse, status_code=201)
async def create_interaction(
    data: InteractionCreate,
    repository: InteractionRepository = Depends(get_interaction_repository),
    product_repository: ProductRepository = Depends(get_product_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    engine: RecommendationEngine = Depends(lambda: app.state.recommendation_engine)
):
    """Create a new interaction and update recommendations."""
    # Verify product and user exist
    product = await product_repository.get_by_id(data.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    user = await user_repository.get_by_id(data.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create interaction
    interaction = Interaction(
        user_id=data.user_id,
        product_id=data.product_id,
        interaction_type=data.interaction_type
    )
    
    # Save interaction
    interaction = await repository.create(interaction)
    
    # Add to recommendation engine
    await engine.add_interaction({
        "user_id": str(data.user_id),
        "item_id": str(data.product_id),
        "item_type": "product",
        "interaction_type": data.interaction_type,
        "timestamp": interaction.timestamp.isoformat(),
        "content": f"{product.name} {product.description} {product.category}"
    })
    
    return interaction


@interaction_router.get("", response_model=List[InteractionResponse])
async def list_interactions(
    repository: InteractionRepository = Depends(get_interaction_repository)
):
    """List all interactions."""
    return await repository.list()


@user_router.get("/{id}/recommendations", response_model=List[ProductRecommendation])
async def get_user_recommendations(
    id: UUID,
    limit: int = 5,
    user_repository: UserRepository = Depends(get_user_repository),
    product_repository: ProductRepository = Depends(get_product_repository),
    engine: RecommendationEngine = Depends(lambda: app.state.recommendation_engine)
):
    """Get recommendations for a user."""
    # Verify user exists
    user = await user_repository.get_by_id(id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get recommendations
    recommendations = await engine.recommend(
        user_id=str(id),
        limit=limit,
        item_type="product"
    )
    
    # Convert to response models
    result = []
    
    for rec in recommendations:
        # Get product
        product_id = UUID(rec["item_id"])
        product = await product_repository.get_by_id(product_id)
        
        if product:
            result.append(
                ProductRecommendation(
                    id=product.id,
                    name=product.name,
                    description=product.description,
                    price=product.price,
                    category=product.category,
                    score=rec["score"]
                )
            )
    
    return result


# Add routers to app
app.include_router(product_router)
app.include_router(user_router)
app.include_router(interaction_router)


# Sample data generation
async def generate_sample_data():
    """Generate sample data for the example."""
    # Create products
    categories = ["Electronics", "Books", "Clothing", "Home", "Sports"]
    
    for i in range(50):
        category = random.choice(categories)
        await product_repository.create(
            Product(
                name=f"{category} Item {i+1}",
                description=f"This is a {category.lower()} item for demonstration purposes.",
                price=round(random.uniform(10.0, 200.0), 2),
                category=category
            )
        )
    
    # Create users
    for i in range(10):
        await user_repository.create(
            User(
                username=f"user{i+1}",
                email=f"user{i+1}@example.com"
            )
        )
    
    # Create interactions
    users = await user_repository.list()
    products = await product_repository.list()
    interaction_types = ["view", "like", "purchase"]
    
    for user in users:
        # Each user interacts with 5-15 products
        num_interactions = random.randint(5, 15)
        user_products = random.sample(products, num_interactions)
        
        for product in user_products:
            interaction_type = random.choices(
                interaction_types,
                weights=[0.7, 0.2, 0.1],  # More views than likes, more likes than purchases
                k=1
            )[0]
            
            await interaction_repository.create(
                Interaction(
                    user_id=user.id,
                    product_id=product.id,
                    interaction_type=interaction_type
                )
            )
    
    # Train recommendation engine
    interactions = []
    for interaction in await interaction_repository.list():
        product = await product_repository.get_by_id(interaction.product_id)
        
        interactions.append({
            "user_id": str(interaction.user_id),
            "item_id": str(interaction.product_id),
            "item_type": "product",
            "interaction_type": interaction.interaction_type,
            "timestamp": interaction.timestamp.isoformat(),
            "content": f"{product.name} {product.description} {product.category}"
        })
    
    # Train the engine
    await app.state.recommendation_engine.train(interactions)
    
    logger.info(f"Generated {len(products)} products, {len(users)} users, and {len(interactions)} interactions")


# Startup and shutdown events
@app.on_event("startup")
async def startup():
    """Initialize recommendation engine and sample data on startup."""
    # Create recommendation engine
    app.state.recommendation_engine = await setup_recommendation_engine()
    
    # Create recommendation router
    router = create_recommendation_router(app.state.recommendation_engine)
    app.include_router(router, prefix="/api")
    
    # Generate sample data
    await generate_sample_data()
    
    logger.info("Recommendation engine initialized with sample data")


@app.on_event("shutdown")
async def shutdown():
    """Close recommendation engine on shutdown."""
    if hasattr(app.state, "recommendation_engine"):
        await app.state.recommendation_engine.close()


# Main function
def main():
    """Run the example application."""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()