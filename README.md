# Security Compliance Assistant

A RAG-based assistant that helps automate vendor security questionnaires and compliance tasks.

## Overview

The Security Compliance Assistant is a tool designed to help security teams efficiently respond to vendor security questionnaires and handle compliance tasks. It leverages Retrieval-Augmented Generation (RAG) to provide accurate, contextual responses based on your organization's security documentation.

## Features

- **Document Ingestion**: Upload and process security documentation (PDF, DOCX, TXT, MD)
- **Vector Search**: Efficient semantic search across your knowledge base
- **AI-Powered Responses**: Generate contextual, accurate responses to security questions
- **API and UI Access**: Interact via a RESTful API or web interface
- **Citation Support**: Responses include citations to source documents

## Architecture

The system consists of the following components:

- **Vector Database**: Stores document embeddings for semantic search (FAISS)
- **Embedding Model**: Converts text to vector representations
- **Document Processing**: Handles parsing, chunking, and metadata extraction
- **Query Engine**: Processes user queries and retrieves relevant context
- **LLM Integration**: Generates responses using retrieved context
- **API Server**: Provides HTTP endpoints for interacting with the system

## Getting Started

### Prerequisites

- Python 3.8+
- Required Python packages (listed in `requirements.txt`)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-org/security-compliance-assistant.git
   cd security-compliance-assistant
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root (optional):
   ```
   # API settings
   API_HOST=0.0.0.0
   API_PORT=8000
   API_DEBUG=True

   # Vector database settings
   VECTOR_DB_TYPE=faiss
   VECTOR_DB_PATH=./data/indexes
   VECTOR_DB_DIMENSIONS=768

   # Embedding settings
   EMBEDDING_MODEL=all-MiniLM-L6-v2

   # LLM settings
   LLM_PROVIDER=mock  # Use "azure_openai" or "anthropic" for production
   LLM_API_KEY=your_api_key_here
   LLM_MODEL=gpt-4
   ```

### Usage

#### Starting the API Server

```
python main.py serve --host 0.0.0.0 --port 8000
```

#### Ingesting Documents

```
# Ingest a single file
python main.py ingest /path/to/document.pdf

# Ingest a directory of documents
python main.py ingest /path/to/documents/ --recursive --extensions .pdf .docx
```

#### Querying the Knowledge Base

```
python main.py query "What is our password policy for third-party vendors?"
```

#### Viewing Settings

```
python main.py settings
```

## API Endpoints

### Document Management

- `POST /ingest/file`: Upload a document file
- `POST /ingest/directory`: Ingest a directory of documents
- `GET /documents`: List all documents
- `GET /documents/{doc_id}`: Get information about a specific document
- `DELETE /documents/{doc_id}`: Delete a document

### Queries

- `POST /query`: Query the knowledge base

### System

- `GET /health`: Health check endpoint
- `GET /settings`: Get system settings

## Web Interface

The web interface is available at `http://localhost:8000/` when the server is running. It provides a user-friendly way to:

- Upload and manage documents
- Submit queries and view responses
- See document sources and citations

## Development

### Project Structure

```
security-compliance-assistant/
├── app/
│   ├── api/              # API routes and endpoints
│   ├── config/           # Configuration settings
│   ├── models/           # Data models
│   ├── services/         # Core services
│   │   ├── providers/    # LLM providers
│   └── static/           # Static web files
├── data/                 # Data directory (created at runtime)
│   ├── indexes/          # Vector stores
│   └── logs/             # Log files
├── main.py               # Main entry point
└── requirements.txt      # Dependencies
```

### Extending LLM Providers

To add a new LLM provider:

1. Create a new provider class in `app/services/providers/`
2. Implement the `BaseLLMProvider` interface
3. Add the provider to the factory in `app/services/providers/factory.py`

## License

[Include license information here]

## Acknowledgements

This project uses the following open-source libraries:
- FastAPI
- FAISS
- SentenceTransformers
- Pydantic
- Uvicorn
