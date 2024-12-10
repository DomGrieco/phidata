# Documentation Agent System

## Overview

The Documentation Agent system is built using the Phidata framework and provides an intelligent interface for querying and retrieving information from the knowledge base. The system combines multiple knowledge bases (PDF and text documents) and uses OpenAI's language models to provide contextual and accurate responses to user queries.

## Architecture

### Components

1. **DocumentationAgent**
   - Core class handling document querying and response generation
   - Manages multiple knowledge bases
   - Integrates with OpenAI for embeddings and responses
   - Provides unified interface for document searching

2. **Knowledge Bases**
   - PDFKnowledgeBase: Handles PDF document retrieval
   - TextKnowledgeBase: Handles text document retrieval
   - CombinedKnowledgeBase: Unifies search across all document types

3. **Vector Database Integration**
   - Uses PgVector (PostgreSQL with pgvector extension)
   - Supports hybrid search capabilities
   - Maintains separate tables for different document types

### Class Structure

```python
class DocumentationAgent:
    def __init__(self):
        # Initialize knowledge bases and assistant
        
    def query(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Process queries and return responses
        
    def search_documents(self, query: str, limit: int = 5) -> Dict[str, Any]:
        # Search for relevant documents
        
    def get_stats(self) -> Dict[str, Any]:
        # Get knowledge base statistics
```

## Implementation Details

### Initialization Process

1. **Directory Setup**
   ```python
   Path("data/pdfs").mkdir(parents=True, exist_ok=True)
   Path("data/text").mkdir(parents=True, exist_ok=True)
   ```

2. **Embedder Configuration**
   ```python
   embedder = OpenAIEmbedder(
       model=settings.embeddings_model,
       dimensions=settings.embeddings_dimensions,
   )
   ```

3. **Knowledge Base Initialization**
   - PDF Knowledge Base with chunking enabled
   - Text Knowledge Base for plain text documents
   - Combined Knowledge Base for unified search

### Query Processing

1. **Document Search**
   - Uses semantic search to find relevant documents
   - Supports hybrid search combining vector and keyword matching
   - Returns most relevant documents based on query

2. **Response Generation**
   - Uses OpenAI's GPT-4 model for response generation
   - Processes response chunks from generator
   - Combines chunks into coherent response

3. **Error Handling**
   - Comprehensive error catching and logging
   - Graceful failure modes
   - Detailed error reporting

## Configuration

### Environment Variables

Required environment variables (defined in `.env`):
```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
DB_HOST=localhost
DB_PORT=5532
DB_NAME=ai
DB_USER=ai
DB_PASSWORD=ai
DB_URL=postgresql+psycopg://ai:ai@localhost:5532/ai

# Vector Database Configuration
VECTOR_DB_TABLE=knowledge_base
EMBEDDINGS_MODEL=text-embedding-3-small
EMBEDDINGS_DIMENSIONS=1536
```

### Vector Database Tables

The system uses separate tables for different document types:
- `pdf_documents`: Stores PDF document embeddings
- `text_documents`: Stores text document embeddings
- `knowledge_base`: Combined knowledge base table

## Usage

### Basic Usage

1. Initialize the agent:
   ```python
   doc_agent = DocumentationAgent()
   ```

2. Query the knowledge base:
   ```python
   response = doc_agent.query("How does feature X work?")
   ```

3. Get knowledge base statistics:
   ```python
   stats = doc_agent.get_stats()
   ```

### Advanced Usage

1. Search with custom limits:
   ```python
   results = doc_agent.search_documents("specific topic", limit=10)
   ```

2. Query with context:
   ```python
   response = doc_agent.query(
       question="How does this relate to X?",
       context={"previous_context": "..."}
   )
   ```

## Response Format

The query response includes:
```python
{
    "status": "success",
    "response": "Generated response text",
    "relevant_documents": [...],  # List of relevant documents
    "metadata": {
        "sources": [...]  # Source references
    }
}
```

## Best Practices

1. **Query Optimization**
   - Be specific in queries
   - Include relevant context
   - Use appropriate search limits

2. **Response Handling**
   - Process response chunks appropriately
   - Handle streaming responses
   - Validate response content

3. **Error Management**
   - Monitor query success rates
   - Log error patterns
   - Handle edge cases gracefully

## Troubleshooting

Common issues and solutions:

1. **Search Issues**
   - Verify database connection
   - Check embedding dimensions
   - Validate query format

2. **Response Generation Issues**
   - Check OpenAI API status
   - Verify API key validity
   - Monitor rate limits

3. **Performance Issues**
   - Monitor search response times
   - Check database indexes
   - Optimize chunk sizes

## Future Improvements

Planned enhancements:
1. Improved context handling
2. Enhanced response formatting
3. Better source attribution
4. Advanced search capabilities
5. Performance optimizations

## Integration Points

The Documentation Agent integrates with:
1. Document Ingestion System
2. Vector Database
3. OpenAI API
4. Knowledge Base Management

## References

- [Phidata Documentation](https://docs.phidata.com/)
- [OpenAI Documentation](https://platform.openai.com/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector) 