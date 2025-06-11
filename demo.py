#!/usr/bin/env python3
"""Demo script for the Security Compliance Assistant.

This script demonstrates how to use the Security Compliance Assistant programmatically.
It shows how to ingest documents, query the knowledge base, and manage documents.
"""
import os
import argparse
import sys
from typing import List

from app.config import settings
from app.models.document import Document, DocumentMetadata
from app.services.ingestion_service import default_ingestion_service
from app.services.query_service import default_query_service


def demo_ingest_sample_document():
    """Demonstrate ingesting a sample document."""
    print("\n=== Ingesting Sample Document ===\n")
    
    # Create a sample document
    sample_text = """
    # Security Policy for Third-Party Vendors

    ## Password Requirements
    All third-party vendors must adhere to the following password requirements:
    - Minimum length: 12 characters
    - Must include uppercase letters, lowercase letters, numbers, and special characters
    - Must be changed every 90 days
    - Must not be reused for at least 12 cycles
    - Accounts must be locked after 5 failed attempts
    
    ## Access Control
    Third-party vendors must implement the principle of least privilege, providing access
    only to the resources necessary for the role. All access must be reviewed quarterly.
    
    ## Data Protection
    Vendors must encrypt all data in transit and at rest using industry-standard encryption
    protocols. Personal data must be handled in accordance with GDPR, CCPA, and other
    applicable regulations.
    
    ## Incident Response
    Vendors must notify us within 24 hours of any security incident that may affect our data.
    A detailed incident report must be provided within 72 hours.
    """
    
    # Create metadata
    metadata = DocumentMetadata(
        filename="security_policy.md",
        title="Security Policy for Third-Party Vendors",
        author="Security Team",
        tags=["security", "policy", "vendor", "compliance"]
    )
    
    # Ingest the document
    document = default_ingestion_service.ingest_text(
        text=sample_text,
        metadata=metadata
    )
    
    # Save the vector store
    default_ingestion_service.save_vector_store()
    
    print(f"Successfully ingested document: {document.metadata.title}")
    print(f"Document ID: {document.doc_id}")
    print(f"Number of chunks: {document.num_chunks}")
    print(f"Tags: {', '.join(document.metadata.tags)}")
    
    return document


def demo_query(queries: List[str] = None):
    """Demonstrate querying the knowledge base.
    
    Args:
        queries: List of queries to run. If None, use default queries.
    """
    print("\n=== Querying the Knowledge Base ===\n")
    
    # Default queries
    if queries is None:
        queries = [
            "What are the password requirements for third-party vendors?",
            "How quickly must vendors report security incidents?",
            "What encryption requirements are there for vendors?",
            "How often must vendor access be reviewed?"
        ]
    
    # Run queries
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 50)
        
        answer, sources, citations = default_query_service.query(query)
        
        print("\nAnswer:")
        print(answer)
        
        if sources:
            print("\nSources:")
            for j, source in enumerate(sources, 1):
                print(f"{j}. {source.get('filename', 'Unknown')}: {source.get('text', '')[:100]}...")


def demo_document_management(doc_id: str = None):
    """Demonstrate document management.
    
    Args:
        doc_id: Document ID to use. If None, ingest a sample document.
    """
    print("\n=== Document Management ===\n")
    
    # If no document ID provided, ingest a sample document
    if doc_id is None:
        document = demo_ingest_sample_document()
        doc_id = document.doc_id
    
    # Query with a filter for the specific document
    print("\nQuerying with document filter:")
    answer, sources, citations = default_query_service.query(
        query="What are the password requirements?",
        filters={"doc_id": doc_id}
    )
    
    print("\nAnswer (filtered to specific document):")
    print(answer)
    
    # Delete the document
    print(f"\nDeleting document with ID: {doc_id}")
    default_ingestion_service.vector_store.delete_chunks(doc_id)
    default_ingestion_service.save_vector_store()
    print("Document deleted")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Security Compliance Assistant Demo")
    
    parser.add_argument(
        "--sample", action="store_true", help="Ingest a sample document"
    )
    parser.add_argument(
        "--query", type=str, nargs="+", help="Queries to run"
    )
    parser.add_argument(
        "--document", type=str, help="Document ID to use for management demo"
    )
    parser.add_argument(
        "--full", action="store_true", help="Run the full demo"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Print settings
    print("\n" + "=" * 50)
    print("Security Compliance Assistant Demo")
    print("=" * 50)
    
    # Load the vector store if it exists
    try:
        default_ingestion_service.vector_store.load()
        print("\nSuccessfully loaded existing vector store")
    except FileNotFoundError:
        print("\nNo existing vector store found. Creating a new one.")
    
    # Run the appropriate demo
    if args.sample:
        demo_ingest_sample_document()
    elif args.query:
        demo_query(args.query)
    elif args.document:
        demo_document_management(args.document)
    elif args.full or len(sys.argv) == 1:
        # Run the full demo
        doc = demo_ingest_sample_document()
        demo_query()
        demo_document_management(doc.doc_id)
    
    print("\n" + "=" * 50)
    print("Demo completed")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
