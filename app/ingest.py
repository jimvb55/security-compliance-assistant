#!/usr/bin/env python3
"""Simple ingestion pipeline for security compliance docs."""
import argparse
from pathlib import Path
import re

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import PyPDF2

CHUNK_SIZE = 500


def extract_text(pdf_path: Path) -> str:
    """Extract all text from a PDF file."""
    reader = PyPDF2.PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE):
    """Yield text chunks of roughly `chunk_size` words."""
    words = re.split(r"\s+", text)
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i : i + chunk_size])


def embed_chunks(chunks, model_name: str = "all-MiniLM-L6-v2"):
    """Embed a list of text chunks using the specified model."""
    try:
        model = SentenceTransformer(model_name)
    except Exception as exc:  # pragma: no cover - network or cache errors
        raise RuntimeError(
            f"Failed to load model '{model_name}'. "
            "Ensure the model is available locally or you have internet access."
        ) from exc
    embeddings = model.encode(list(chunks))
    return embeddings


def build_index(embeddings):
    """Create a FAISS index from embedding vectors."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index


def save_index(index, index_path: Path):
    """Persist FAISS index to disk."""
    faiss.write_index(index, str(index_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PDF and build embedding index")
    parser.add_argument("pdf", type=Path, help="Path to PDF document")
    parser.add_argument("--output", "-o", type=Path, default=Path("index.faiss"), help="Index file path")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="SentenceTransformer model name or local path")
    args = parser.parse_args()

    text = extract_text(args.pdf)
    chunks = list(chunk_text(text))
    embeddings = embed_chunks(chunks, model_name=args.model)
    index = build_index(np.array(embeddings).astype("float32"))
    save_index(index, args.output)
    print(f"Ingested {len(chunks)} chunks. Index saved to {args.output}")


if __name__ == "__main__":
    main()
