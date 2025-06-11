# Security Compliance Assistant

This repository contains the initial requirements for a Retrieval-Augmented Generation (RAG) assistant that helps speed up vendor security questionnaires.

## Ingestion Script

`app/ingest.py` is a small prototype for ingesting policy PDFs. It extracts text, chunks it into approximately 500-word segments, embeds the chunks using a sentence-transformers model, and stores them in a FAISS index file.

### Setup

```bash
pip install -r requirements.txt
```

### Usage

```bash
python app/ingest.py path/to/policy.pdf -o index.faiss
```

The script prints the number of chunks ingested and writes the FAISS index to the specified output file.

This is an early proof of concept and does not include authentication or production hardening.
