"""
Content Generation Example using the Uno AI framework.

This example demonstrates how to use the content generation engine to:
1. Index content into both vector and graph stores
2. Generate content using different RAG strategies
3. Summarize text with different formats and modes
4. Use the content generation API with FastAPI

Requirements:
- PostgreSQL with pgvector extension
- PostgreSQL with Apache AGE extension
- OpenAI API key (or Anthropic API key)
"""

import asyncio
import os
import logging
from typing import Dict, List, Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from uno.ai.content_generation import ContentEngine, integrate_content_generation
from uno.ai.content_generation.engine import (
    ContentType, ContentMode, ContentFormat, RAGStrategy
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONNECTION_STRING = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/uno_ai"
)

# API keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Sample data for indexing
SAMPLE_CONTENT = [
    {
        "content": "Apache AGE is a PostgreSQL extension that provides graph database functionality. "
                   "It enables users to leverage graph query capabilities within PostgreSQL.",
        "entity_id": "apache_age_overview",
        "entity_type": "documentation",
        "metadata": {"source": "Apache AGE docs", "topic": "graph_database"}
    },
    {
        "content": "pgvector is a PostgreSQL extension for vector similarity search. "
                   "It provides vector data types and similarity operators that enable efficient "
                   "similarity searches for machine learning applications.",
        "entity_id": "pgvector_overview",
        "entity_type": "documentation",
        "metadata": {"source": "pgvector docs", "topic": "vector_search"}
    },
    {
        "content": "PostgreSQL is an advanced open-source relational database system. "
                   "It supports both SQL and JSON querying, has robust transaction support, "
                   "and offers many advanced features like custom extensions.",
        "entity_id": "postgresql_overview",
        "entity_type": "documentation",
        "metadata": {"source": "PostgreSQL docs", "topic": "database"}
    }
]

# Graph relationships
GRAPH_RELATIONSHIPS = [
    {
        "from_id": "apache_age_overview",
        "to_id": "postgresql_overview",
        "type": "EXTENDS",
        "properties": {"relationship_type": "extension"}
    },
    {
        "from_id": "pgvector_overview",
        "to_id": "postgresql_overview",
        "type": "EXTENDS",
        "properties": {"relationship_type": "extension"}
    }
]


async def direct_usage_example():
    """Example of directly using the ContentEngine."""
    logger.info("Starting direct usage example")
    
    # Create content engine
    engine = ContentEngine(
        connection_string=DB_CONNECTION_STRING,
        llm_provider="openai" if OPENAI_API_KEY else "anthropic",
        llm_model="gpt-3.5-turbo" if OPENAI_API_KEY else "claude-2",
        api_key=OPENAI_API_KEY or ANTHROPIC_API_KEY,
        use_graph_db=True,
        graph_schema="knowledge_graph",
        rag_strategy=RAGStrategy.HYBRID
    )
    
    # Initialize engine
    await engine.initialize()
    
    try:
        # Index sample content
        for item in SAMPLE_CONTENT:
            await engine.index_content(
                content=item["content"],
                entity_id=item["entity_id"],
                entity_type=item["entity_type"],
                metadata=item["metadata"]
            )
        
        # Add relationships to graph
        if engine.use_graph_db and engine.graph_connection:
            for rel in GRAPH_RELATIONSHIPS:
                await engine.index_content(
                    content="Relationship",
                    entity_id=f"rel_{rel['from_id']}_{rel['to_id']}",
                    entity_type="relationship",
                    metadata={},
                    graph_relationships=[rel]
                )
        
        # Generate content with different strategies
        for strategy in [RAGStrategy.VECTOR_ONLY, RAGStrategy.GRAPH_ONLY, RAGStrategy.HYBRID]:
            logger.info(f"Generating content with {strategy} strategy")
            
            result = await engine.generate_content(
                prompt="Explain how PostgreSQL extensions enhance database capabilities",
                content_type=ContentType.TEXT,
                mode=ContentMode.BALANCED,
                format=ContentFormat.MARKDOWN,
                max_length=300,
                rag_strategy=strategy,
                max_context_items=3
            )
            
            logger.info(f"Generated content ({strategy}):\n{result['content']}\n")
            logger.info(f"Context sources: {result['context_sources']}\n")
        
        # Create a summary
        text_to_summarize = "\n\n".join([item["content"] for item in SAMPLE_CONTENT])
        
        summary = await engine.summarize(
            text=text_to_summarize,
            max_length=150,
            format=ContentFormat.PLAIN,
            mode=ContentMode.PRECISE,
            bullet_points=False
        )
        
        logger.info(f"Summary:\n{summary['content']}\n")
        
        # Bullet point summary
        bullets = await engine.summarize(
            text=text_to_summarize,
            max_length=200,
            format=ContentFormat.MARKDOWN,
            mode=ContentMode.BALANCED,
            bullet_points=True
        )
        
        logger.info(f"Bullet points:\n{bullets['content']}\n")
        
    finally:
        # Clean up
        await engine.close()


async def api_example():
    """Example of using the content generation API with FastAPI."""
    logger.info("Starting API example")
    
    app = FastAPI(title="Uno AI Content Generation API")
    
    # Basic templates for a simple web interface
    templates = Jinja2Templates(directory="templates")
    
    # Create templates directory if it doesn't exist
    os.makedirs("templates", exist_ok=True)
    
    # Create a simple index.html template
    with open("templates/index.html", "w") as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Content Generation Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        textarea, select, input { width: 100%; padding: 8px; }
        button { padding: 10px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        .result { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; }
        .loading { display: none; }
    </style>
</head>
<body>
    <h1>Content Generation Demo</h1>
    
    <div class="tabs">
        <button onclick="showTab('generate')">Generate Content</button>
        <button onclick="showTab('summarize')">Summarize Text</button>
    </div>
    
    <div id="generate" class="tab-content">
        <h2>Generate Content</h2>
        <form id="generateForm">
            <div class="form-group">
                <label for="prompt">Prompt:</label>
                <textarea id="prompt" name="prompt" rows="3" required></textarea>
            </div>
            
            <div class="form-group">
                <label for="contentType">Content Type:</label>
                <select id="contentType" name="contentType">
                    <option value="text">Text</option>
                    <option value="summary">Summary</option>
                    <option value="bullets">Bullets</option>
                    <option value="title">Title</option>
                    <option value="description">Description</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="mode">Mode:</label>
                <select id="mode" name="mode">
                    <option value="balanced">Balanced</option>
                    <option value="creative">Creative</option>
                    <option value="precise">Precise</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="format">Format:</label>
                <select id="format" name="format">
                    <option value="plain">Plain Text</option>
                    <option value="markdown">Markdown</option>
                    <option value="html">HTML</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="strategy">RAG Strategy:</label>
                <select id="strategy" name="strategy">
                    <option value="hybrid">Hybrid</option>
                    <option value="vector_only">Vector Only</option>
                    <option value="graph_only">Graph Only</option>
                    <option value="adaptive">Adaptive</option>
                </select>
            </div>
            
            <button type="submit">Generate</button>
        </form>
        
        <div id="generateLoading" class="loading">Generating content...</div>
        <div id="generateResult" class="result"></div>
    </div>
    
    <div id="summarize" class="tab-content" style="display:none;">
        <h2>Summarize Text</h2>
        <form id="summarizeForm">
            <div class="form-group">
                <label for="text">Text to Summarize:</label>
                <textarea id="text" name="text" rows="6" required></textarea>
            </div>
            
            <div class="form-group">
                <label for="summaryMode">Mode:</label>
                <select id="summaryMode" name="summaryMode">
                    <option value="balanced">Balanced</option>
                    <option value="creative">Creative</option>
                    <option value="precise">Precise</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="summaryFormat">Format:</label>
                <select id="summaryFormat" name="summaryFormat">
                    <option value="plain">Plain Text</option>
                    <option value="markdown">Markdown</option>
                    <option value="html">HTML</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="bulletPoints">Style:</label>
                <select id="bulletPoints" name="bulletPoints">
                    <option value="false">Paragraph</option>
                    <option value="true">Bullet Points</option>
                </select>
            </div>
            
            <button type="submit">Summarize</button>
        </form>
        
        <div id="summarizeLoading" class="loading">Summarizing text...</div>
        <div id="summarizeResult" class="result"></div>
    </div>
    
    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.style.display = 'none';
            });
            document.getElementById(tabName).style.display = 'block';
        }
        
        document.getElementById('generateForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const prompt = document.getElementById('prompt').value;
            const contentType = document.getElementById('contentType').value;
            const mode = document.getElementById('mode').value;
            const format = document.getElementById('format').value;
            const strategy = document.getElementById('strategy').value;
            
            document.getElementById('generateLoading').style.display = 'block';
            document.getElementById('generateResult').innerHTML = '';
            
            try {
                const response = await fetch('/api/content/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        prompt: prompt,
                        content_type: contentType,
                        mode: mode,
                        format: format,
                        rag_strategy: strategy,
                        max_length: 500
                    }),
                });
                
                const data = await response.json();
                
                let resultHTML = '<h3>Generated Content:</h3>';
                resultHTML += `<div>${data.content}</div>`;
                resultHTML += `<p><strong>Sources:</strong> ${data.context_sources ? data.context_sources.join(', ') : 'None'}</p>`;
                
                document.getElementById('generateResult').innerHTML = resultHTML;
            } catch (error) {
                document.getElementById('generateResult').innerHTML = `<p>Error: ${error.message}</p>`;
            } finally {
                document.getElementById('generateLoading').style.display = 'none';
            }
        });
        
        document.getElementById('summarizeForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const text = document.getElementById('text').value;
            const mode = document.getElementById('summaryMode').value;
            const format = document.getElementById('summaryFormat').value;
            const bulletPoints = document.getElementById('bulletPoints').value === 'true';
            
            document.getElementById('summarizeLoading').style.display = 'block';
            document.getElementById('summarizeResult').innerHTML = '';
            
            try {
                const response = await fetch('/api/content/summarize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: text,
                        mode: mode,
                        format: format,
                        bullet_points: bulletPoints,
                        max_length: 200
                    }),
                });
                
                const data = await response.json();
                
                let resultHTML = '<h3>Summary:</h3>';
                resultHTML += `<div>${data.content}</div>`;
                resultHTML += `<p><strong>Original Length:</strong> ${data.original_length} characters</p>`;
                resultHTML += `<p><strong>Summary Length:</strong> ${data.summary_length} characters</p>`;
                resultHTML += `<p><strong>Reduction Ratio:</strong> ${Math.round(data.reduction_ratio * 100)}%</p>`;
                
                document.getElementById('summarizeResult').innerHTML = resultHTML;
            } catch (error) {
                document.getElementById('summarizeResult').innerHTML = `<p>Error: ${error.message}</p>`;
            } finally {
                document.getElementById('summarizeLoading').style.display = 'none';
            }
        });
    </script>
</body>
</html>
        """)
    
    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    
    # Integrate content generation API
    integrate_content_generation(
        app=app,
        connection_string=DB_CONNECTION_STRING,
        embedding_model="default",
        llm_provider="openai" if OPENAI_API_KEY else "anthropic",
        llm_model="gpt-3.5-turbo" if OPENAI_API_KEY else "claude-2",
        api_key=OPENAI_API_KEY or ANTHROPIC_API_KEY,
        use_graph_db=True,
        graph_schema="knowledge_graph",
        path_prefix="/api"
    )
    
    # Start the server
    logger.info("Starting FastAPI server on http://localhost:8000")
    logger.info("Use Ctrl+C to stop the server")
    
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Run the examples."""
    if not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
        logger.error("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        return
    
    # Run direct usage example
    await direct_usage_example()
    
    # Run API example
    # Uncomment to run the API example
    # await api_example()


if __name__ == "__main__":
    asyncio.run(main())