#!/usr/bin/env python
"""
Vector search demo script.

This script demonstrates the vector search capabilities of the Uno framework
from the command line.
"""

import asyncio
import argparse
import logging
import json
from typing import List, Dict, Any, Optional

from uno.settings import uno_settings
from uno.dependencies import configure_di
from uno.vector_search.examples import (
    create_example_documents,
    simple_vector_search_example,
    rag_prompt_example,
    batch_update_example
)


async def run_demo(args):
    """Run the vector search demo based on command-line arguments."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    
    # Configure dependency injection
    configure_di()
    
    # Handle different commands
    if args.command == "setup":
        logger.info("Creating example documents...")
        document_ids = await create_example_documents()
        logger.info(f"Created {len(document_ids)} example documents with IDs:")
        for doc_id in document_ids:
            logger.info(f"  - {doc_id}")
    
    elif args.command == "search":
        if not args.query:
            logger.error("No query provided. Use --query to specify a search query.")
            return
        
        logger.info(f"Searching for: '{args.query}'")
        results = await simple_vector_search_example(
            query_text=args.query,
            limit=args.limit
        )
        
        logger.info(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            logger.info(f"\n[{i}] {result['title']} (Score: {result['similarity']})")
            logger.info(f"    {result['snippet']}")
    
    elif args.command == "rag":
        if not args.query:
            logger.error("No query provided. Use --query to specify a question.")
            return
        
        logger.info(f"Generating RAG prompt for: '{args.query}'")
        prompt = await rag_prompt_example(args.query)
        
        logger.info("\nSystem Prompt:")
        logger.info(prompt["system_prompt"])
        
        logger.info("\nUser Prompt with RAG Context:")
        logger.info(prompt["user_prompt"])
        
        # Save to file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(prompt, f, indent=2)
            logger.info(f"\nSaved RAG prompt to {args.output}")
    
    elif args.command == "update":
        logger.info("Running batch update of vector embeddings...")
        stats = await batch_update_example()
        logger.info("Update statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
    
    else:
        logger.error(f"Unknown command: {args.command}")


def main():
    """Parse arguments and run the demo."""
    parser = argparse.ArgumentParser(description="Vector search demo")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Create example documents")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Perform vector search")
    search_parser.add_argument("--query", "-q", type=str, help="Search query")
    search_parser.add_argument("--limit", "-l", type=int, default=5, help="Maximum results to return")
    
    # RAG command
    rag_parser = subparsers.add_parser("rag", help="Generate RAG prompt for LLM")
    rag_parser.add_argument("--query", "-q", type=str, help="Question to answer")
    rag_parser.add_argument("--output", "-o", type=str, help="Output file for RAG prompt")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update vector embeddings")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run the demo asynchronously
    asyncio.run(run_demo(args))


if __name__ == "__main__":
    main()