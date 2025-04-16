"""Test script to verify the domain router schema generation works correctly."""

from src.uno.domain.api_integration import DomainRouter
from src.uno.meta.entities import MetaType
from src.uno.meta.domain_services import MetaTypeService

def test_schema_generation():
    """Test generating schemas from the MetaType entity."""
    # Create a router for the MetaType entity
    router = DomainRouter(
        entity_type=MetaType,
        service_type=MetaTypeService,
        prefix="/meta-types",
        tags=["Meta"],
        generate_schemas=True
    )
    
    # If we get here without errors, it worked
    print("Schema generation successful!")
    print(f"Created Response DTO: {router.response_dto}")
    print(f"Created Create DTO: {router.create_dto}")
    print(f"Created Update DTO: {router.update_dto}")

if __name__ == "__main__":
    test_schema_generation()