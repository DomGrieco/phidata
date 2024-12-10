# Knowledge Base Application

A centralized knowledge base chatbot system for legal matter and spend management software teams, built using the Phidata framework.

## Features

- Multi-agent system for specialized knowledge domains
- PDF and document processing capabilities
- Vector database for efficient information retrieval
- Persistent memory and chat history
- API for integration with other systems
- Streamlit UI for testing and development
- React frontend for production use

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start the PostgreSQL database:
```bash
docker run -d \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgvolume:/var/lib/postgresql/data \
  -p 5532:5432 \
  --name pgvector \
  phidata/pgvector:16
```

5. Run the application:
```bash
# For development with Streamlit
streamlit run ui/streamlit/app.py

# For API development
uvicorn app.main:app --reload
```

## Project Structure

```
knowledge_base_app/
├── app/                        # Main application directory
│   ├── agents/                # Agent definitions
│   ├── knowledge/             # Knowledge base implementations
│   ├── storage/              # Storage implementations
│   ├── tools/                # Custom tools
│   ├── schemas/             # Pydantic models
│   └── utils/               # Utility functions
├── tests/                   # Test directory
├── scripts/                # Utility scripts
└── ui/                    # Frontend applications
```

## Development

1. Add new documents to `data/pdfs/` directory
2. Run document ingestion:
```bash
python scripts/ingest_docs.py
```

3. Start development server:
```bash
uvicorn app.main:app --reload
```

## Testing

Run tests with:
```bash
pytest
```

## Contributing

1. Create a new branch
2. Make your changes
3. Run tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 