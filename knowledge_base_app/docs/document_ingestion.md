# Document Ingestion System Documentation

## Overview

The document ingestion system is built using the Phidata framework and provides functionality to process, embed, and store various document types in a vector database for efficient retrieval and querying. The system currently supports PDF and text documents, with a modular design that allows for easy extension to other document types.

## Architecture

### Components

1. **DocumentProcessor**
   - Core class handling document ingestion
   - Manages multiple knowledge bases
   - Provides unified interface for document operations

2. **Knowledge Bases**
   - PDFKnowledgeBase: Handles PDF document processing
   - TextKnowledgeBase: Handles text document processing
   - Each knowledge base maintains its own vector database table

3. **Vector Database**
   - Uses PgVector (PostgreSQL with pgvector extension)
   - Stores document embeddings and metadata
   - Supports efficient similarity search

### Directory Structure

```
knowledge_base_app/
├── data/
│   ├── pdfs/     # PDF document storage
│   └── text/     # Text document storage
├── app/
│   └── utils/
│       └── document_processor.py  # Main document processing logic
└── scripts/
    └── ingest_docs.py            # Document ingestion script
```

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

The system creates separate tables for different document types:
- `pdf_documents`: Stores PDF document embeddings
- `text_documents`: Stores text document embeddings

## Usage

### Basic Usage

1. Place documents in appropriate directories:
   ```bash
   # For PDF documents
   cp your_document.pdf data/pdfs/
   
   # For text documents
   cp your_document.txt data/text/
   ```

2. Run the ingestion script:
   ```bash
   python scripts/ingest_docs.py
   ```

### Advanced Usage

1. Clear existing documents before ingestion:
   ```bash
   python scripts/ingest_docs.py --clear-existing
   ```

2. Specify custom document paths:
   ```bash
   python scripts/ingest_docs.py --pdf-path custom/pdf/path --text-path custom/text/path
   ```

## Implementation Details

### Document Processing

#### PDF Documents
- Uses `PDFReader` with chunking enabled
- Automatically splits large PDFs into manageable chunks
- Maintains document structure and context
- Creates embeddings for each chunk

#### Text Documents
- Processes plain text files
- Creates embeddings for text content
- Supports metadata extraction

### Vector Storage

Each document type uses a dedicated PgVector instance with:
- Custom table name
- OpenAI embeddings configuration
- Configurable dimensions
- Efficient similarity search capabilities

### Error Handling

The system implements comprehensive error handling:
- Graceful failure for missing directories
- Exception catching for processing errors
- Fallback mechanisms for counting documents
- Detailed error reporting

## Monitoring and Metrics

The system provides document count metrics:
- Total number of documents
- Count by document type (PDF, text)
- Processing status and success rates

## Best Practices

1. **Document Organization**
   - Keep documents organized by type
   - Use consistent naming conventions
   - Maintain document metadata

2. **Performance Optimization**
   - Process documents in batches
   - Monitor vector database size
   - Regular maintenance of unused embeddings

3. **Error Management**
   - Monitor ingestion logs
   - Verify document counts after ingestion
   - Regular validation of stored documents

## Extending the System

To add support for new document types:

1. Create a new knowledge base class:
   ```python
   from phi.knowledge import Knowledge
   
   class NewTypeKnowledgeBase(Knowledge):
       # Implement required methods
       pass
   ```

2. Add to DocumentProcessor:
   ```python
   self.new_type_knowledge = NewTypeKnowledgeBase(
       path="data/new_type",
       vector_db=PgVector(
           table_name="new_type_documents",
           db_url=settings.db_url,
           embedder=OpenAIEmbedder(
               model=settings.embeddings_model,
               dimensions=settings.embeddings_dimensions,
           ),
       ),
   )
   ```

3. Implement ingestion method:
   ```python
   def ingest_new_type(self, path: str = "data/new_type") -> Dict[str, Any]:
       # Implement ingestion logic
       pass
   ```

## Troubleshooting

Common issues and solutions:

1. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection credentials
   - Ensure pgvector extension is installed

2. **OpenAI API Issues**
   - Verify API key is valid
   - Check API rate limits
   - Monitor API usage

3. **Document Processing Errors**
   - Check file permissions
   - Verify file formats
   - Monitor system resources

## Future Improvements

Planned enhancements:
1. Support for additional document types
2. Improved chunking strategies
3. Enhanced metadata extraction
4. Batch processing optimization
5. Advanced error recovery mechanisms

## References

- [Phidata Documentation](https://docs.phidata.com/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings Documentation](https://platform.openai.com/docs/guides/embeddings)
</rewritten_file> 