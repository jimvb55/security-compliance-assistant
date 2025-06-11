#!/usr/bin/env python3
"""
Query script for the Security Compliance Assistant.

This script provides a command-line interface for querying the knowledge base.
"""
import argparse
import os
import sys
import cmd
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.config import settings
from app.services.query_service import QueryService, default_query_service
from app.services.retrieval_service import RetrievalService, default_retrieval_service
from app.services.vector_store import create_vector_store


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Query the Security Compliance Assistant knowledge base"
    )
    
    # Optional arguments
    parser.add_argument(
        "query", nargs="?", type=str,
        help="Query string (if not provided, enter interactive mode)"
    )
    parser.add_argument(
        "-p", "--index-path", type=str,
        help="Path to the vector store index (default: data/indexes/<index_name>)"
    )
    parser.add_argument(
        "-i", "--index-name", type=str, default="default",
        help="Name of the index to query (default: default)"
    )
    parser.add_argument(
        "-n", "--num-results", type=int, default=settings.DEFAULT_NUM_RESULTS,
        help=f"Number of results to retrieve (default: {settings.DEFAULT_NUM_RESULTS})"
    )
    parser.add_argument(
        "-m", "--min-score", type=float, default=settings.DEFAULT_MIN_SCORE,
        help=f"Minimum similarity score for results (default: {settings.DEFAULT_MIN_SCORE})"
    )
    parser.add_argument(
        "-t", "--tag", type=str,
        help="Filter results by tag"
    )
    parser.add_argument(
        "-c", "--category", type=str,
        help="Filter results by category"
    )
    parser.add_argument(
        "--show-sources", action="store_true",
        help="Show source documents and excerpts in the results"
    )
    
    return parser.parse_args()


def create_query_service(args):
    """Create a query service based on the command-line arguments.
    
    Args:
        args: Command-line arguments.
        
    Returns:
        QueryService instance.
    """
    # Create vector store
    vector_store = create_vector_store(index_name=args.index_name)
    
    # Load vector store index if it exists
    index_path = args.index_path
    
    try:
        vector_store.load(index_path)
        print(f"Loaded index with {len(vector_store.chunks)} chunks")
    except FileNotFoundError:
        print(f"No index found at {index_path or vector_store.get_default_path()}")
        print("You need to ingest some documents first using the ingest.py script.")
        sys.exit(1)
    
    # Create retrieval service
    retrieval_service = RetrievalService(vector_store=vector_store)
    
    # Create query service
    query_service = QueryService(retrieval_service=retrieval_service)
    
    return query_service


def process_query(
    query_service: QueryService,
    query: str,
    num_results: int = 5,
    min_score: float = 0.6,
    show_sources: bool = False,
    filters: Optional[Dict] = None
) -> None:
    """Process a query and display the results.
    
    Args:
        query_service: The query service.
        query: The query string.
        num_results: Maximum number of results to return.
        min_score: Minimum similarity score for results.
        show_sources: Whether to show source documents and excerpts.
        filters: Optional filters for the search.
    """
    # Query the knowledge base
    answer, results, citations = query_service.query(
        query=query,
        num_results=num_results,
        min_score=min_score,
        filters=filters
    )
    
    # Display the answer
    print("\n" + "=" * 80)
    print(f"Q: {query}")
    print("=" * 80 + "\n")
    print(answer)
    
    # Display sources if requested
    if show_sources and results:
        print("\n" + "-" * 80)
        print("Sources:")
        print("-" * 80 + "\n")
        
        for i, result in enumerate(results):
            metadata = result["metadata"]
            score = result["score"]
            
            print(f"[{i+1}] Score: {score:.4f}")
            print(f"    Document: {metadata['filename']}")
            
            if metadata.get("title"):
                print(f"    Title: {metadata['title']}")
            
            if metadata.get("author"):
                print(f"    Author: {metadata['author']}")
            
            print(f"    Excerpt: {result['text'][:300]}..." if len(result['text']) > 300 else f"    Excerpt: {result['text']}")
            print()


class QueryShell(cmd.Cmd):
    """Interactive shell for querying the knowledge base."""
    
    intro = "Welcome to the Security Compliance Assistant interactive shell. Type 'help' for a list of commands."
    prompt = "Query> "
    
    def __init__(
        self,
        query_service: QueryService,
        num_results: int = 5,
        min_score: float = 0.6,
        show_sources: bool = False
    ):
        """Initialize the query shell.
        
        Args:
            query_service: The query service.
            num_results: Maximum number of results to return.
            min_score: Minimum similarity score for results.
            show_sources: Whether to show source documents and excerpts.
        """
        super().__init__()
        self.query_service = query_service
        self.num_results = num_results
        self.min_score = min_score
        self.show_sources = show_sources
        self.filters = {}
    
    def default(self, line: str) -> bool:
        """Handle queries that don't match a command.
        
        Args:
            line: The input line.
            
        Returns:
            True to continue, False to exit.
        """
        if line.strip() == "exit" or line.strip() == "quit":
            return self.do_exit(line)
        
        process_query(
            query_service=self.query_service,
            query=line,
            num_results=self.num_results,
            min_score=self.min_score,
            show_sources=self.show_sources,
            filters=self.filters if self.filters else None
        )
        
        return True
    
    def do_results(self, arg: str) -> bool:
        """Set the number of results to return.
        
        Args:
            arg: The number of results.
            
        Returns:
            True to continue.
        """
        try:
            num = int(arg.strip())
            if num < 1:
                print("Number of results must be at least 1")
            else:
                self.num_results = num
                print(f"Number of results set to {num}")
        except ValueError:
            print("Invalid number")
        
        return True
    
    def do_score(self, arg: str) -> bool:
        """Set the minimum similarity score.
        
        Args:
            arg: The minimum score.
            
        Returns:
            True to continue.
        """
        try:
            score = float(arg.strip())
            if score < 0 or score > 1:
                print("Score must be between 0 and 1")
            else:
                self.min_score = score
                print(f"Minimum score set to {score}")
        except ValueError:
            print("Invalid score")
        
        return True
    
    def do_sources(self, arg: str) -> bool:
        """Toggle whether to show sources.
        
        Args:
            arg: Not used.
            
        Returns:
            True to continue.
        """
        self.show_sources = not self.show_sources
        print(f"Show sources: {self.show_sources}")
        return True
    
    def do_tag(self, arg: str) -> bool:
        """Set a tag filter.
        
        Args:
            arg: The tag to filter by.
            
        Returns:
            True to continue.
        """
        if arg.strip():
            self.filters["tags"] = arg.strip()
            print(f"Tag filter set to: {arg.strip()}")
        else:
            if "tags" in self.filters:
                del self.filters["tags"]
            print("Tag filter cleared")
        
        return True
    
    def do_category(self, arg: str) -> bool:
        """Set a category filter.
        
        Args:
            arg: The category to filter by.
            
        Returns:
            True to continue.
        """
        if arg.strip():
            self.filters["category"] = arg.strip()
            print(f"Category filter set to: {arg.strip()}")
        else:
            if "category" in self.filters:
                del self.filters["category"]
            print("Category filter cleared")
        
        return True
    
    def do_filters(self, arg: str) -> bool:
        """Show or clear all filters.
        
        Args:
            arg: "clear" to clear all filters, empty to show current filters.
            
        Returns:
            True to continue.
        """
        if arg.strip().lower() == "clear":
            self.filters = {}
            print("All filters cleared")
        else:
            if self.filters:
                print("Current filters:")
                for key, value in self.filters.items():
                    print(f"  {key}: {value}")
            else:
                print("No filters set")
        
        return True
    
    def do_exit(self, arg: str) -> bool:
        """Exit the shell.
        
        Args:
            arg: Not used.
            
        Returns:
            False to exit.
        """
        print("Goodbye!")
        return False
    
    def do_help(self, arg: str) -> bool:
        """Show help message.
        
        Args:
            arg: The command to get help for.
            
        Returns:
            True to continue.
        """
        if not arg.strip():
            print("\nAvailable commands:")
            print("  results N     - Set the number of results to return")
            print("  score N       - Set the minimum similarity score (0-1)")
            print("  sources       - Toggle whether to show sources")
            print("  tag TAG       - Set a tag filter (empty to clear)")
            print("  category CAT  - Set a category filter (empty to clear)")
            print("  filters       - Show current filters")
            print("  filters clear - Clear all filters")
            print("  exit/quit     - Exit the shell")
            print("  help          - Show this help message")
            print("\nType any other text to submit a query.\n")
        else:
            cmd.Cmd.do_help(self, arg)
        
        return True


def main():
    """Main entry point."""
    args = parse_args()
    
    # Create query service
    query_service = create_query_service(args)
    
    # Set up filters
    filters = {}
    if args.tag:
        filters["tags"] = args.tag
    if args.category:
        filters["category"] = args.category
    
    # Process query or enter interactive mode
    if args.query:
        process_query(
            query_service=query_service,
            query=args.query,
            num_results=args.num_results,
            min_score=args.min_score,
            show_sources=args.show_sources,
            filters=filters if filters else None
        )
    else:
        # Interactive mode
        shell = QueryShell(
            query_service=query_service,
            num_results=args.num_results,
            min_score=args.min_score,
            show_sources=args.show_sources
        )
        
        # Set initial filters
        shell.filters = filters
        
        # Start the shell
        shell.cmdloop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
