"""Command-line script for ingesting documents into the knowledge base."""
import argparse
import os
import sys
from typing import List, Optional

from app.config import settings
from app.services.ingestion_service import default_ingestion_service


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ingest documents into the knowledge base")
    
    # Add arguments
    parser.add_argument(
        "path", type=str, help="Path to file or directory to ingest"
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="Recursively traverse directories"
    )
    parser.add_argument(
        "--extensions", "-e", type=str, nargs="+", 
        help="File extensions to include (e.g., .pdf .docx .txt)"
    )
    parser.add_argument(
        "--tag", "-t", type=str, action="append", 
        help="Tags to apply to the document(s). Can be used multiple times."
    )
    parser.add_argument(
        "--clear", "-c", action="store_true", 
        help="Clear the knowledge base before ingestion"
    )
    
    return parser.parse_args()


def normalize_extensions(extensions: Optional[List[str]]) -> Optional[List[str]]:
    """Normalize file extensions.
    
    Args:
        extensions: List of file extensions.
        
    Returns:
        Normalized list of file extensions.
    """
    if not extensions:
        return None
    
    return [
        ext if ext.startswith(".") else f".{ext}" 
        for ext in extensions
    ]


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_args()
    
    # Check if path exists
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist")
        sys.exit(1)
    
    # Clear the knowledge base if requested
    if args.clear:
        print("Clearing the knowledge base...")
        default_ingestion_service.clear_vector_store()
    
    # Normalize extensions
    extensions = normalize_extensions(args.extensions)
    
    # Ingest file or directory
    if os.path.isfile(args.path):
        # Ingest file
        print(f"Ingesting file: {args.path}")
        document = default_ingestion_service.ingest_file(args.path)
        
        # Add tags if provided
        if args.tag:
            document.metadata.tags.extend(args.tag)
            document = default_ingestion_service.ingest_file(
                args.path, 
                metadata=document.metadata,
                doc_id=document.doc_id
            )
        
        # Save the vector store
        default_ingestion_service.save_vector_store()
        
        print(f"Successfully ingested document: {document.metadata.filename}")
        print(f"Document ID: {document.doc_id}")
        print(f"Number of chunks: {document.num_chunks}")
    else:
        # Ingest directory
        print(f"Ingesting directory: {args.path}")
        documents = default_ingestion_service.ingest_directory(
            directory_path=args.path,
            recursive=args.recursive,
            file_extensions=extensions,
        )
        
        # Add tags if provided
        if args.tag and documents:
            # Re-ingest with tags
            updated_documents = []
            for doc in documents:
                doc.metadata.tags.extend(args.tag)
                updated_doc = default_ingestion_service.ingest_file(
                    doc.metadata.file_path, 
                    metadata=doc.metadata,
                    doc_id=doc.doc_id
                )
                updated_documents.append(updated_doc)
            documents = updated_documents
        
        # Save the vector store
        default_ingestion_service.save_vector_store()
        
        print(f"Successfully ingested {len(documents)} documents")
        print(f"Total chunks: {sum(doc.num_chunks for doc in documents)}")


if __name__ == "__main__":
    main()
