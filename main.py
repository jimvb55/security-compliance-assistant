"""Main entry point for the Security Compliance Assistant."""
import argparse
import logging
import os
import sys
import uvicorn

from app.config import settings
from app.api.app import app as fastapi_app


def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs(settings.LOGS_DIR, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(settings.LOGS_DIR, "app.log")),
        ],
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Security Compliance Assistant")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument(
        "--host", type=str, default=settings.API_HOST, help="Host to bind to"
    )
    serve_parser.add_argument(
        "--port", type=int, default=settings.API_PORT, help="Port to bind to"
    )
    serve_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload"
    )
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents")
    ingest_parser.add_argument(
        "path", type=str, help="Path to file or directory to ingest"
    )
    ingest_parser.add_argument(
        "--recursive", action="store_true", help="Recursively traverse directories"
    )
    ingest_parser.add_argument(
        "--extensions", type=str, nargs="+", help="File extensions to include"
    )
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the knowledge base")
    query_parser.add_argument(
        "query", type=str, help="Query string"
    )
    query_parser.add_argument(
        "--num-results", type=int, default=settings.DEFAULT_NUM_RESULTS,
        help="Number of results to return"
    )
    query_parser.add_argument(
        "--min-score", type=float, default=settings.DEFAULT_MIN_SCORE,
        help="Minimum similarity score"
    )
    
    # Settings command
    settings_parser = subparsers.add_parser("settings", help="Print settings")
    
    return parser.parse_args()


def main():
    """Main entry point."""
    # Set up logging
    setup_logging()
    
    # Print startup message
    print("\n" + "=" * 50)
    print("Security Compliance Assistant")
    print("=" * 50 + "\n")
    
    # Parse arguments
    args = parse_args()
    
    # Execute command
    if args.command == "serve":
        # Start the API server
        uvicorn.run(
            "app.api.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    elif args.command == "ingest":
        # Import services
        from app.services.ingestion_service import default_ingestion_service
        
        # Check if path exists
        if not os.path.exists(args.path):
            print(f"Error: Path '{args.path}' does not exist")
            sys.exit(1)
        
        # Ingest file or directory
        if os.path.isfile(args.path):
            # Ingest file
            print(f"Ingesting file: {args.path}")
            document = default_ingestion_service.ingest_file(args.path)
            default_ingestion_service.save_vector_store()
            print(f"Successfully ingested document: {document.metadata.filename}")
            print(f"Document ID: {document.doc_id}")
            print(f"Number of chunks: {document.num_chunks}")
        else:
            # Ingest directory
            print(f"Ingesting directory: {args.path}")
            documents = default_ingestion_service.ingest_directory(
                args.path,
                recursive=args.recursive,
                file_extensions=args.extensions,
            )
            default_ingestion_service.save_vector_store()
            print(f"Successfully ingested {len(documents)} documents")
            print(f"Total chunks: {sum(doc.num_chunks for doc in documents)}")
    elif args.command == "query":
        # Import services
        from app.services.query_service import default_query_service
        
        # Query the knowledge base
        print(f"Query: {args.query}")
        answer, sources, citations = default_query_service.query(
            query=args.query,
            num_results=args.num_results,
            min_score=args.min_score,
        )
        
        # Print answer
        print("\nAnswer:")
        print(answer)
        
        # Print sources
        if sources:
            print("\nSources:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source.get('filename', 'Unknown')}: {source.get('text', '')[:100]}...")
    elif args.command == "settings":
        # Print settings
        settings.print_settings()
    else:
        # Print help
        parse_args().print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
