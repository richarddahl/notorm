"""
Example demonstrating the use of KnowledgeConstructor for automated knowledge graph construction.

This example shows how to extract entities and relationships from text and
build a knowledge graph that can be integrated with other AI features.
"""

import asyncio
import logging
from typing import List

from uno.ai.graph_integration import (
    KnowledgeConstructor,
    KnowledgeConstructorConfig,
    EntityExtractionMethod,
    RelationshipExtractionMethod,
    ValidationMethod,
    ConstructionPipeline,
    TextSource
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def knowledge_graph_construction_example():
    """
    Demonstrate knowledge graph construction from text.
    
    This example:
    1. Creates a knowledge constructor with custom configuration
    2. Prepares sample text sources with business content
    3. Extracts entities and relationships using different methods
    4. Constructs a knowledge graph from the extracted information
    5. Performs queries on the constructed graph
    """
    # Database connection string
    connection_string = "postgresql://postgres:postgres@localhost:5432/knowledge_db"
    
    # Configure the knowledge constructor
    config = KnowledgeConstructorConfig(
        graph_name="business_knowledge_graph",
        spacy_model="en_core_web_sm",
        deduplication_enabled=True,
        validation_enabled=True,
        # Custom entity patterns for business domain
        custom_entity_patterns={
            "PRODUCT": [
                r"\b[A-Z][a-zA-Z]+ (v\d+\.\d+|Suite|Platform|API)\b",
                r"\b[A-Z][a-zA-Z]+ (Pro|Enterprise|Cloud)\b"
            ],
            "TECHNOLOGY": [
                r"\b(AI|ML|NLP|API|REST|GraphQL|SQL|NoSQL|Kubernetes|Docker)\b",
                r"\b(Python|Java|JavaScript|TypeScript|C\+\+|Rust|Go)\b"
            ]
        },
        # Custom relationship patterns for business domain
        custom_relationship_patterns={
            "USES": [
                r"(\b[A-Z][a-zA-Z]+ (Inc|Corp|Corporation|Company|Ltd|LLC)\b) uses (\b(AI|ML|NLP|API|REST|GraphQL|SQL|NoSQL|Kubernetes|Docker)\b)",
                r"(\b[A-Z][a-z]+ [A-Z][a-z]+\b) uses (\b[A-Z][a-zA-Z]+ (Pro|Enterprise|Cloud)\b)"
            ],
            "DEVELOPS": [
                r"(\b[A-Z][a-zA-Z]+ (Inc|Corp|Corporation|Company|Ltd|LLC)\b) develops (\b[A-Z][a-zA-Z]+ (v\d+\.\d+|Suite|Platform|API)\b)",
                r"(\b[A-Z][a-zA-Z]+ (Inc|Corp|Corporation|Company|Ltd|LLC)\b) created (\b[A-Z][a-zA-Z]+ (Pro|Enterprise|Cloud)\b)"
            ]
        }
    )
    
    # Create a knowledge constructor
    constructor = KnowledgeConstructor(connection_string, config, logger=logger)
    
    try:
        # Initialize the constructor
        await constructor.initialize()
        
        # Sample text sources
        text_sources = [
            TextSource(
                id="business_article_1",
                content="""
                TechCorp Inc is a leading technology company located in San Francisco. 
                The company was founded by John Smith in 2010. TechCorp Inc develops AI Platform 
                that uses NLP for analyzing business data. Sarah Johnson is the current CEO of 
                TechCorp Inc, and she previously worked for DataSys Corporation.
                
                MegaSoft Corporation, based in Seattle, is known for their MegaSoft Cloud product.
                They are competitors with TechCorp Inc but recently announced a partnership 
                to integrate MegaSoft Cloud with AI Platform. MegaSoft Corporation uses Kubernetes
                for their infrastructure and has over 5000 employees.
                """,
                source_type="article",
                metadata={"domain": "technology", "publisher": "Tech Today"}
            ),
            TextSource(
                id="business_press_release",
                content="""
                NEW YORK, June 15, 2024 - Finance Systems Ltd, a fintech company based in New York,
                announced today the acquisition of PayTech Inc for $500 million. The deal will allow
                Finance Systems Ltd to expand its market presence and integrate PayTech's 
                Payment Processing API into its existing Financial Suite v3.2.
                
                "This acquisition strengthens our position in the payment processing space," said
                Michael Brown, CEO of Finance Systems Ltd. "We're excited to welcome the PayTech Inc
                team to our company."
                
                PayTech Inc, founded in 2015 by David Chen, has developed cutting-edge payment
                technology that uses AI for fraud detection. The company is headquartered in 
                Boston and employs approximately 200 people.
                """,
                source_type="press_release",
                metadata={"domain": "finance", "date": "2024-06-15"}
            )
        ]
        
        # Define different pipelines for different extraction methods
        pipelines = {
            "rule_based": ConstructionPipeline(
                entity_extraction_method=EntityExtractionMethod.RULE_BASED,
                relationship_extraction_method=RelationshipExtractionMethod.PATTERN_BASED,
                validation_method=ValidationMethod.CONFIDENCE_THRESHOLD,
                entity_confidence_threshold=0.6,
                relationship_confidence_threshold=0.7
            ),
            "spacy": ConstructionPipeline(
                entity_extraction_method=EntityExtractionMethod.SPACY_NER,
                relationship_extraction_method=RelationshipExtractionMethod.DEPENDENCY_PARSING,
                validation_method=ValidationMethod.CONFIDENCE_THRESHOLD,
                entity_confidence_threshold=0.5,
                relationship_confidence_threshold=0.6
            )
        }
        
        # Extract knowledge using different methods
        logger.info("Extracting knowledge with rule-based method...")
        rule_based_result = await constructor.extract_knowledge(
            text_sources[0], pipelines["rule_based"]
        )
        
        logger.info(f"Extracted {len(rule_based_result.entities)} entities and "
                   f"{len(rule_based_result.relationships)} relationships using rule-based method")
        
        # Print some extracted entities
        logger.info("Sample entities from rule-based extraction:")
        for entity in rule_based_result.entities[:3]:
            logger.info(f"  - {entity.type}: {entity.text} (confidence: {entity.confidence:.2f})")
        
        # Try SpaCy-based extraction if available
        try:
            logger.info("Extracting knowledge with SpaCy-based method...")
            spacy_result = await constructor.extract_knowledge(
                text_sources[1], pipelines["spacy"]
            )
            
            logger.info(f"Extracted {len(spacy_result.entities)} entities and "
                       f"{len(spacy_result.relationships)} relationships using SpaCy-based method")
        except Exception as e:
            logger.warning(f"SpaCy-based extraction failed: {e}")
        
        # Construct knowledge graph from all text sources
        logger.info("Constructing knowledge graph from all text sources...")
        construction_result = await constructor.construct_knowledge_graph(
            text_sources, pipelines["rule_based"]
        )
        
        logger.info(f"Knowledge graph constructed successfully: "
                   f"{construction_result.entity_count} entities, "
                   f"{construction_result.relationship_count} relationships")
        
        # Query the graph
        logger.info("Querying the knowledge graph...")
        
        # Find all companies
        companies = await constructor.query_graph("""
            MATCH (c:ORGANIZATION)
            WHERE c.properties->>'type' = 'ORGANIZATION'
            RETURN c
        """)
        
        logger.info(f"Found {len(companies)} companies in the knowledge graph")
        for company in companies:
            logger.info(f"  - {company.get('properties', {}).get('text', 'Unknown')}")
        
        # Find relationships between companies
        relationships = await constructor.query_graph("""
            MATCH (c1:ORGANIZATION)-[r]-(c2:ORGANIZATION)
            RETURN c1.properties->>'text' AS company1, 
                   type(r) AS relationship, 
                   c2.properties->>'text' AS company2
        """)
        
        logger.info(f"Found {len(relationships)} relationships between companies")
        for rel in relationships:
            logger.info(f"  - {rel.get('company1')} {rel.get('relationship')} {rel.get('company2')}")
        
        # Find all technologies used by companies
        technologies = await constructor.query_graph("""
            MATCH (c:ORGANIZATION)-[:USES]->(t:TECHNOLOGY)
            RETURN c.properties->>'text' AS company, t.properties->>'text' AS technology
        """)
        
        logger.info(f"Found {len(technologies)} technology usage relationships")
        for tech in technologies:
            logger.info(f"  - {tech.get('company')} uses {tech.get('technology')}")
        
        # Export graph for visualization
        logger.info("Exporting knowledge graph...")
        export_data = await constructor.export_graph(format="json")
        
        logger.info(f"Exported knowledge graph with {export_data.get('metadata', {}).get('node_count', 0)} nodes "
                   f"and {export_data.get('metadata', {}).get('relationship_count', 0)} relationships")
    
    except Exception as e:
        logger.error(f"Error in knowledge graph construction example: {e}")
    
    finally:
        # Close the constructor
        await constructor.close()
        logger.info("Knowledge graph construction example completed")


async def integrate_with_semantic_search_example():
    """
    Demonstrate integration of knowledge graph with semantic search.
    
    This example shows how to:
    1. Construct a knowledge graph from text
    2. Use the graph to enhance semantic search results
    3. Provide context-aware recommendations
    """
    # Database connection string
    connection_string = "postgresql://postgres:postgres@localhost:5432/knowledge_db"
    
    # Create a knowledge constructor with default configuration
    config = KnowledgeConstructorConfig(graph_name="integrated_knowledge_graph")
    constructor = KnowledgeConstructor(connection_string, config, logger=logger)
    
    try:
        # Initialize the constructor
        await constructor.initialize()
        
        # Sample text about AI technologies and companies
        ai_text = TextSource(
            id="ai_technologies",
            content="""
            Machine Learning is a subset of Artificial Intelligence that focuses on developing
            systems that can learn from data. Deep Learning is a type of Machine Learning
            based on neural networks with multiple layers. Natural Language Processing (NLP)
            is the field of AI that deals with interactions between computers and human language.
            
            OpenAI develops GPT-4, which is a large language model based on the Transformer
            architecture. Google developed BERT, which revolutionized NLP. BERT uses a 
            bidirectional transformer approach, while GPT uses a unidirectional transformer.
            
            TensorFlow is a machine learning framework developed by Google, while PyTorch
            is maintained by Facebook. Both frameworks are used for developing deep learning models,
            but PyTorch is often preferred for research due to its dynamic computation graph.
            """,
            source_type="educational",
            metadata={"domain": "artificial_intelligence", "topic": "technologies"}
        )
        
        # Construct knowledge graph
        logger.info("Constructing AI knowledge graph...")
        await constructor.extract_knowledge(ai_text)
        construction_result = await constructor.construct_knowledge_graph([ai_text])
        
        logger.info(f"AI knowledge graph constructed: "
                   f"{construction_result.entity_count} entities, "
                   f"{construction_result.relationship_count} relationships")
        
        # Semantic search integration
        logger.info("Integrating with semantic search...")
        
        # Sample search query
        search_query = "deep learning frameworks"
        
        # Find relevant entities in the knowledge graph
        graph_results = await constructor.query_graph(f"""
            MATCH (n)
            WHERE n.properties->>'text' CONTAINS 'deep learning'
               OR n.properties->>'text' CONTAINS 'framework'
               OR n.properties->>'text' CONTAINS 'PyTorch'
               OR n.properties->>'text' CONTAINS 'TensorFlow'
            RETURN n
        """)
        
        logger.info(f"Found {len(graph_results)} entities in knowledge graph relevant to query: '{search_query}'")
        
        # Extract entity IDs for further exploration
        entity_ids = [result.get('id') for result in graph_results if 'id' in result]
        
        # Find related entities and relationships
        if entity_ids:
            # Get the first entity ID for demonstration
            entity_id = entity_ids[0]
            
            related_entities = await constructor.query_graph(f"""
                MATCH (n)-[r]-(related)
                WHERE id(n) = '{entity_id}'
                RETURN related, type(r) AS relationship_type
            """)
            
            logger.info(f"Found {len(related_entities)} entities related to the main search results")
            
            # Simulate enhanced search results with graph context
            enhanced_results = {
                "query": search_query,
                "direct_matches": [r.get('properties', {}).get('text') for r in graph_results],
                "related_concepts": [
                    {
                        "text": r.get('related', {}).get('properties', {}).get('text'),
                        "relationship": r.get('relationship_type')
                    }
                    for r in related_entities
                ]
            }
            
            logger.info("Enhanced search results with knowledge graph context:")
            logger.info(f"  - Direct matches: {enhanced_results['direct_matches']}")
            logger.info(f"  - Related concepts: {[r['text'] for r in enhanced_results['related_concepts']]}")
    
    except Exception as e:
        logger.error(f"Error in integration example: {e}")
    
    finally:
        # Close the constructor
        await constructor.close()
        logger.info("Integration example completed")


async def document_analysis_example():
    """
    Demonstrate using knowledge constructor for analyzing documents.
    
    This example shows how to:
    1. Extract structured knowledge from business documents
    2. Analyze relationships between entities
    3. Generate insights based on the knowledge graph
    """
    # Database connection string
    connection_string = "postgresql://postgres:postgres@localhost:5432/knowledge_db"
    
    # Create a knowledge constructor with custom configuration for document analysis
    config = KnowledgeConstructorConfig(
        graph_name="document_analysis_graph",
        # Add custom entity types for document analysis
        custom_entity_patterns={
            "PROJECT": [
                r"\b(Project|Initiative) [A-Z][a-zA-Z]+\b",
                r"\b[A-Z][a-zA-Z]+ (Project|Initiative)\b"
            ],
            "DEPARTMENT": [
                r"\b(Sales|Marketing|Finance|HR|IT|Engineering|Research) Department\b",
                r"\bDepartment of (Sales|Marketing|Finance|HR|IT|Engineering|Research)\b"
            ],
            "METRIC": [
                r"\b(Revenue|Cost|Profit|ROI|Conversion Rate|Engagement Rate)\b",
                r"\b\d+(\.\d+)? (percent|%) (increase|decrease|growth)\b"
            ]
        }
    )
    
    constructor = KnowledgeConstructor(connection_string, config, logger=logger)
    
    try:
        # Initialize the constructor
        await constructor.initialize()
        
        # Sample business document
        business_report = TextSource(
            id="quarterly_report_q2_2024",
            content="""
            Q2 2024 Business Report - TechCorp Inc
            
            Executive Summary:
            TechCorp Inc achieved a 15% increase in revenue during Q2 2024, exceeding our target
            of 12%. The Sales Department reported record growth in the enterprise segment, while
            the Marketing Department successfully launched three new campaigns. Project Phoenix, 
            our digital transformation initiative, is now 75% complete and has already delivered
            cost savings of $2.3M.
            
            Department Performance:
            - Sales Department: 18% increase in new customers, with Enterprise Sales exceeding
              targets by 22%. John Smith was promoted to VP of Sales.
            - Marketing Department: 24% increase in Conversion Rate, with the new campaign for
              AI Platform generating 3500 qualified leads.
            - Engineering Department: Delivered four major releases of MegaSoft Cloud, reducing
              critical bugs by 35%.
            - Finance Department: Reduced operational costs by 8% while supporting Project Phoenix.
            
            Key Projects:
            - Project Phoenix: Digital transformation led by Sarah Johnson, 75% complete
            - Cloud Migration Initiative: Led by Engineering Department, 92% complete
            - Marketing Automation Project: 45% complete, showing promising early results with
              a 24% improvement in campaign efficiency.
            
            Outlook:
            TechCorp Inc expects continued growth in Q3 2024, with projected Revenue increase
            of 14-16%. The partnership with MegaSoft Corporation will expand to include joint
            development of AI-enhanced cloud solutions.
            """,
            source_type="business_report",
            metadata={"company": "TechCorp Inc", "period": "Q2 2024", "confidential": False}
        )
        
        # Define pipeline specialized for business document analysis
        document_pipeline = ConstructionPipeline(
            entity_extraction_method=EntityExtractionMethod.RULE_BASED,
            relationship_extraction_method=RelationshipExtractionMethod.PATTERN_BASED,
            entity_confidence_threshold=0.6,
            relationship_confidence_threshold=0.7,
            # Focus on business-specific entity types
            entity_types=["ORGANIZATION", "PERSON", "PROJECT", "DEPARTMENT", "METRIC"]
        )
        
        # Extract knowledge from the business report
        logger.info("Analyzing business document...")
        extraction_result = await constructor.extract_knowledge(
            business_report, document_pipeline
        )
        
        logger.info(f"Extracted {len(extraction_result.entities)} entities and "
                   f"{len(extraction_result.relationships)} relationships from business report")
        
        # Analyze entities by type
        entity_types = {}
        for entity in extraction_result.entities:
            if entity.type not in entity_types:
                entity_types[entity.type] = []
            entity_types[entity.type].append(entity.text)
        
        logger.info("Entity analysis by type:")
        for entity_type, entities in entity_types.items():
            logger.info(f"  - {entity_type}: {len(entities)} entities")
            logger.info(f"    Examples: {', '.join(entities[:3])}")
        
        # Construct knowledge graph
        logger.info("Constructing document knowledge graph...")
        construction_result = await constructor.construct_knowledge_graph(
            [business_report], document_pipeline
        )
        
        logger.info(f"Document knowledge graph constructed: "
                   f"{construction_result.entity_count} entities, "
                   f"{construction_result.relationship_count} relationships")
        
        # Generate insights from the knowledge graph
        logger.info("Generating insights from document knowledge graph...")
        
        # Find departments and their metrics
        department_metrics = await constructor.query_graph("""
            MATCH (d:DEPARTMENT)-[r]-(m:METRIC)
            RETURN d.properties->>'text' AS department, 
                   m.properties->>'text' AS metric,
                   type(r) AS relationship
        """)
        
        logger.info(f"Department performance metrics: {len(department_metrics)} relationships found")
        for item in department_metrics:
            logger.info(f"  - {item.get('department')}: {item.get('metric')}")
        
        # Find projects and associated people
        project_people = await constructor.query_graph("""
            MATCH (p:PROJECT)-[r]-(person:PERSON)
            RETURN p.properties->>'text' AS project, 
                   person.properties->>'text' AS person,
                   type(r) AS relationship
        """)
        
        logger.info(f"Project leadership: {len(project_people)} relationships found")
        for item in project_people:
            logger.info(f"  - {item.get('project')} - {item.get('person')}")
        
        # Generate summary of findings
        logger.info("Document analysis complete. Key insights:")
        logger.info("  1. Identified key projects and their completion status")
        logger.info("  2. Mapped department performance metrics")
        logger.info("  3. Associated key personnel with projects and departments")
        logger.info("  4. Extracted business metrics and performance indicators")
    
    except Exception as e:
        logger.error(f"Error in document analysis example: {e}")
    
    finally:
        # Close the constructor
        await constructor.close()
        logger.info("Document analysis example completed")


# Main function to run all examples
async def main():
    """Run all knowledge construction examples."""
    logger.info("Starting knowledge graph construction examples")
    
    # Run the basic example
    logger.info("\n\n=== Basic Knowledge Graph Construction Example ===\n")
    await knowledge_graph_construction_example()
    
    # Run the integration example
    logger.info("\n\n=== Semantic Search Integration Example ===\n")
    await integrate_with_semantic_search_example()
    
    # Run the document analysis example
    logger.info("\n\n=== Document Analysis Example ===\n")
    await document_analysis_example()
    
    logger.info("All examples completed")


if __name__ == "__main__":
    # Run the event loop
    asyncio.run(main())