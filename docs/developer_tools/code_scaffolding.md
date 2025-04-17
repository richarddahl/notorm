# Code Scaffolding with Uno

This guide explains how to use Uno's code scaffolding system to quickly create new features following the domain-driven design patterns used throughout the framework.

## Getting Started

The scaffolding system allows you to:

1. Create entire projects with a predefined structure
2. Create individual features with all required components
3. Customize the generated code to fit your needs

## Creating New Projects

To create a new Uno project, use the scaffolding tool:

```bash
# Using the CLI directly
python -m uno.devtools.cli.main scaffold new my_project

# With custom options
python -m uno.devtools.cli.main scaffold new my_project --template standard --database postgresql
```

### Project Options

- `--template`, `-t`: Project template to use (default: "standard")
- `--database`, `-d`: Database backend (default: "postgresql")
- `--no-api`: Skip API setup
- `--no-ddd`: Skip domain-driven design structure
- `--output`, `-o`: Output directory

## Creating Features

Once you have a project, you can scaffold features with the necessary components:

```bash
# Basic usage
python -m uno.devtools.cli.main scaffold feature product

# With domain name
python -m uno.devtools.cli.main scaffold feature product --domain ecommerce
```

This creates a complete feature with:

1. **Domain Entity**: Pure domain model (`product_entity.py`)
2. **Database Model**: SQLAlchemy ORM model (`product_model.py`)
3. **Repository**: Data access interface and implementation (`product_repository.py`)
4. **Service**: Business logic implementation (`product_service.py`)
5. **Endpoints**: FastAPI REST endpoints (`product_endpoints.py`)
6. **Tests**: Unit and integration tests

### Feature Options

- `--domain`, `-d`: Domain name (creates feature in a subdomain)
- `--no-entity`: Skip entity creation
- `--no-model`: Skip database model creation
- `--no-repository`: Skip repository creation
- `--no-service`: Skip service creation
- `--no-endpoint`: Skip endpoint creation
- `--no-tests`: Skip test creation
- `--project`, `-p`: Project directory (if not in project directory)

## Understanding the Generated Code

### Domain Entity

The domain entity is created using the Domain-Driven Design pattern:

```python
@dataclass
class Product(AggregateRoot[str]):
    """
    Product domain entity.
    
    This class represents the domain entity for Product following DDD principles.
    """
    
    name: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    # ...
```

- Inherits from `AggregateRoot` for aggregate roots
- Uses Python dataclasses for clean, readable code
- Includes domain validation and business rules
- Contains domain-specific methods
- Pure domain model, no infrastructure concerns

### Database Model

The database model uses SQLAlchemy ORM:

```python
class ProductModel(Base):
    """SQLAlchemy model for Product."""
    
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    # ...
```

- Maps to database tables
- Defines columns, relationships, and constraints
- Handles database-specific concerns

### Repository

The repository handles data access:

```python
class ProductRepository(Repository[Product, str], ProductRepositoryProtocol):
    """SQLAlchemy implementation of Product repository."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize the repository."""
        self.db = UnoRepository(db_session, ProductModel)
        self.entity_class = Product
    
    async def get_by_id(self, id: str) -> Result[Optional[Product]]:
        # ...
```

- Abstracts data access logic
- Handles conversion between domain entities and database models
- Uses the Result pattern for error handling
- Implements the Repository interface

### Service

The service implements business logic:

```python
class ProductService(DomainService[Product, str], ProductServiceProtocol):
    """Service for managing Product entities."""
    
    def __init__(
        self, 
        repository: ProductRepositoryProtocol,
        event_dispatcher: Optional[EventDispatcher] = None,
        logger: Optional[logging.Logger] = None
    ):
        # ...
    
    async def create(self, data: Dict[str, Any]) -> Result[Product]:
        # ...
```

- Implements business logic and operations
- Uses dependency injection for repositories
- Emits domain events
- Handles validation and error cases

### Endpoints

The endpoints create the REST API:

```python
@router.post("", response_model=ProductResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreateDTO,
    service: ProductServiceProtocol = Depends(get_product_service)
):
    """Create a new product."""
    # ...
```

- Creates FastAPI endpoints for CRUD operations
- Includes DTO (Data Transfer Object) definitions
- Handles validation and error responses
- Uses dependency injection for services

## Customizing Templates

You can customize the generated code by modifying the templates in:

```
src/uno/devtools/templates/feature/
```

The templates use Jinja2 for templating logic, allowing for dynamic content generation.

## Best Practices

1. **Use Domain Subfolders**: Group related features under domains (e.g., `--domain ecommerce`)
2. **Add Business Logic**: Extend the generated code with your specific business rules
3. **Keep Domain Pure**: Avoid adding infrastructure concerns to domain entities
4. **Extend Entity Tests**: Add tests for your business rules and validation
5. **Follow the Pattern**: Use the generated structure as a guide for consistency

## Demonstration

Here's a complete example workflow:

```bash
# Create a new project
python -m uno.devtools.cli.main scaffold new ecommerce

# Navigate to the project
cd ecommerce

# Scaffold a product feature in the store domain
python -m uno.devtools.cli.main scaffold feature product --domain store

# Scaffold an order feature
python -m uno.devtools.cli.main scaffold feature order --domain store

# Scaffold a user feature without tests
python -m uno.devtools.cli.main scaffold feature user --domain auth --no-tests
```

After scaffolding, you'll need to:

1. Add relationships between entities
2. Implement specific business logic
3. Create database migrations
4. Register endpoints with the main application

## Troubleshooting

### Common Issues

1. **Template Not Found**: Check that you're in the correct directory or specify with `--project`
2. **Import Errors**: You may need to add imports for custom types
3. **File Already Exists**: The tool won't overwrite existing files

### Getting Help

For more help with the scaffolding tool:

```bash
python -m uno.devtools.cli.main scaffold --help
python -m uno.devtools.cli.main scaffold feature --help
```