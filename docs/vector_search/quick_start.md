# Vector Search Quick Start

This guide will help you get started with vector search functionality in uno.

## Prerequisites

- Docker environment set up (see Docker First documentation in the project root)
- uno installed and configured

## Step 1: Start the Docker Environment

First, ensure your Docker environment is running:

```bash
hatch run dev:docker-setup
```

## Step 2: Create Example Documents

Create some example documents with vector embeddings:

```bash
hatch run dev:vector-demo setup
```

## Step 3: Try Vector Search

Search through the example documents:

```bash
# Search for documents related to PostgreSQL
hatch run dev:vector-demo search --query "How does PostgreSQL handle vector search?"

# Search for documents related to FastAPI
hatch run dev:vector-demo search --query "What are the key features of FastAPI?"
```

## Step 4: Try RAG (Retrieval-Augmented Generation)

Generate a prompt suitable for an LLM with relevant context:

```bash
hatch run dev:vector-demo rag --query "Explain how Python handles different data types" --output rag_prompt.json
```

## API Integration

Alternatively, you can use the API endpoints for vector search:

### Basic Vector Search

```bash
curl -X POST "http://localhost:8000/api/vector/search/documents" \
  -H "Content-Type: application/json" \
  -d '{"query": "How does PostgreSQL support vector search?", "limit": 3, "threshold": 0.6}'
```

### Generate Embeddings

```bash
curl -X POST "http://localhost:8000/api/vector/embed" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test sentence for embedding generation."}'
```

### Create RAG Prompts

```bash
curl -X POST "http://localhost:8000/api/vector/rag/prompt" \
  -H "Content-Type: application/json" \
  -d '{```

"query": "How do I use FastAPI with dependency injection?",
"system_prompt": "You are a helpful programming assistant.",
"limit": 3,
"threshold": 0.6
```
  }'
```

## Advanced Usage

For more advanced usage, see the following documentation:

- [Vector Search Overview](overview.md)
- [pgVector Integration](pgvector_integration.md)
- [Dependency Injection](dependency_injection.md)
- [RAG Implementation](rag.md)
- [API Usage](api_usage.md)
- [Event-Driven Updates](event_driven.md)