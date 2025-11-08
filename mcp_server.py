#!/usr/bin/env python3
"""
MCP Server for CV-RAG System
Exposes CV search functionality to Cursor and Claude Desktop via Model Context Protocol
"""
import asyncio
import logging
from typing import Optional, Dict, Any
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import config
from cv_indexer import CVIndexer

# Setup logging - use absolute path to avoid read-only filesystem errors
LOG_FILE = Path(__file__).parent / "mcp_server.log"
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    filename=str(LOG_FILE)
)
logger = logging.getLogger("mcp_server")

# Initialize the CV indexer
logger.info("Initializing CV indexer...")
try:
    indexer = CVIndexer()
    logger.info("CV indexer initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize indexer: {e}")
    raise

# Create MCP server
server = Server("cv-rag-system")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available tools for the MCP client
    """
    return [
        Tool(
            name="search_cvs",
            description=(
                "Semantically search through Bekk's CV database. "
                "Use this to find candidates with specific skills, experience, or qualifications. "
                "Returns relevant CV excerpts with metadata about the candidates. "
                "Optionally filter by office/department. "
                "Example queries: 'Senior konsulent med Azure erfaring', 'TOGAF og enterprise architecture', "
                "'Python og machine learning erfaring'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'Senior konsulent med Azure erfaring')"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": f"Number of results to return (default: {config.DEFAULT_SEARCH_RESULTS}, max: {config.MAX_SEARCH_RESULTS})",
                        "default": config.DEFAULT_SEARCH_RESULTS,
                        "minimum": 1,
                        "maximum": config.MAX_SEARCH_RESULTS
                    },
                    "office": {
                        "type": "string",
                        "description": (
                            "Optional: Filter by office or department. "
                            "Use 'Trondheim' for Trondheim office, or department names like "
                            "'Teknologi', 'Design', 'Management Consulting', 'Oppdrag' for Oslo offices."
                        )
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_cv_stats",
            description=(
                "Get statistics about the indexed CV database, including total number of CVs, "
                "chunks, and embedding model information."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_cv_by_name",
            description=(
                "Retrieve all chunks from a specific CV by candidate name. "
                "Use this when you need complete information about a specific candidate. "
                "The name should match the filename (e.g., 'ola-nordmann.md')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Filename of the CV (e.g., 'ola-nordmann.md')"
                    }
                },
                "required": ["source"]
            }
        ),
        Tool(
            name="list_all_candidates",
            description=(
                "Get a complete overview of all candidates in the database with their names, departments, and years of experience. "
                "Use this to get a high-level view before doing detailed searches. "
                "Returns a list of all available CVs with metadata including years_of_experience."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_candidates_metadata",
            description=(
                "Get metadata (name, office, years of experience, source) for multiple candidates at once. "
                "Much more efficient than calling get_cv_by_name() multiple times. "
                "Provide a list of candidate names or source filenames. "
                "Useful when you have a list of candidates and need to quickly check their experience levels."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "candidates": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": (
                            "List of candidate names or source filenames (e.g., ['Ola Nordmann', 'kari-hansen.json']). "
                            "Can mix names and source filenames."
                        )
                    }
                },
                "required": ["candidates"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Handle tool calls from MCP clients
    """
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "search_cvs":
            query = arguments.get("query")
            n_results = arguments.get("n_results", config.DEFAULT_SEARCH_RESULTS)
            office = arguments.get("office")
            
            if not query:
                return [TextContent(
                    type="text",
                    text="Error: 'query' parameter is required"
                )]
            
            # Build metadata filter if office is specified
            filter_metadata = None
            if office:
                filter_metadata = {"office": office}
                logger.info(f"Filtering by office: {office}")
            
            # Perform search
            results = indexer.search(query, n_results=n_results, filter_metadata=filter_metadata)
            
            # Format results
            response = format_search_results(query, results, office_filter=office)
            
            return [TextContent(
                type="text",
                text=response
            )]
        
        elif name == "get_cv_stats":
            stats = indexer.get_stats()
            
            response = f"""CV Database Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total CVs indexed: {stats['unique_cvs']}
Total chunks: {stats['total_chunks']}
Embedding model: {stats['embedding_model']}
Collection: {stats['collection_name']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            return [TextContent(
                type="text",
                text=response
            )]
        
        elif name == "list_all_candidates":
            # Get all documents
            all_results = indexer.collection.get(
                include=['metadatas']
            )
            
            # Extract unique candidates with all metadata
            candidates = {}
            for metadata in all_results['metadatas']:
                name = metadata.get('cv_name', 'Unknown')
                office = metadata.get('office', 'Unknown')
                source = metadata.get('source', '')
                years_exp = metadata.get('years_of_experience')
                
                if name not in candidates:
                    candidates[name] = {
                        'name': name,
                        'office': office,
                        'source': source,
                        'years_of_experience': years_exp
                    }
            
            # Format response
            response = f"""Complete Candidate Overview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total candidates: {len(candidates)}

"""
            
            # Group by office
            by_office = {}
            for candidate in candidates.values():
                office = candidate['office'] or 'Unknown'
                if office not in by_office:
                    by_office[office] = []
                by_office[office].append(candidate)
            
            for office, candidate_list in sorted(by_office.items()):
                response += f"\n{office} ({len(candidate_list)} candidates):\n"
                for candidate in sorted(candidate_list, key=lambda x: x['name']):
                    exp_str = f" ({candidate['years_of_experience']:.1f} år)" if candidate['years_of_experience'] is not None else ""
                    response += f"  • {candidate['name']}{exp_str}\n"
            
            response += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            response += "\n\nUse search_cvs() to find candidates with specific skills."
            response += "\nUse get_candidates_metadata() to get detailed info for multiple candidates."
            
            return [TextContent(
                type="text",
                text=response
            )]
        
        elif name == "get_candidates_metadata":
            candidates_input = arguments.get("candidates", [])
            
            if not candidates_input:
                return [TextContent(
                    type="text",
                    text="Error: 'candidates' parameter is required (list of candidate names or source filenames)"
                )]
            
            # Get all documents to build lookup maps
            all_results = indexer.collection.get(
                include=['metadatas']
            )
            
            # Build lookup maps: name -> metadata, source -> metadata
            by_name = {}
            by_source = {}
            
            for metadata in all_results['metadatas']:
                name = metadata.get('cv_name', 'Unknown')
                source = metadata.get('source', '')
                
                # Store first occurrence (all chunks have same metadata)
                if name not in by_name:
                    by_name[name] = metadata
                if source and source not in by_source:
                    by_source[source] = metadata
            
            # Match input candidates
            found_candidates = []
            not_found = []
            
            for candidate_input in candidates_input:
                # Try to match by name first
                matched_meta = None
                if candidate_input in by_name:
                    matched_meta = by_name[candidate_input]
                elif candidate_input in by_source:
                    matched_meta = by_source[candidate_input]
                else:
                    # Try case-insensitive name match
                    for name, meta in by_name.items():
                        if name.lower() == candidate_input.lower():
                            matched_meta = meta
                            break
                
                if matched_meta:
                    found_candidates.append({
                        'input': candidate_input,
                        'name': matched_meta.get('cv_name', 'Unknown'),
                        'office': matched_meta.get('office', 'Unknown'),
                        'source': matched_meta.get('source', ''),
                        'years_of_experience': matched_meta.get('years_of_experience')
                    })
                else:
                    not_found.append(candidate_input)
            
            # Format response
            response_parts = [
                f"Candidate Metadata ({len(found_candidates)} found)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                ""
            ]
            
            for candidate in found_candidates:
                exp_str = f"{candidate['years_of_experience']:.1f} år" if candidate['years_of_experience'] is not None else "Ikke tilgjengelig"
                office_str = f" | {candidate['office']}" if candidate['office'] else ""
                response_parts.extend([
                    f"• {candidate['name']}{office_str}",
                    f"  Erfaring: {exp_str}",
                    f"  Source: {candidate['source']}",
                    ""
                ])
            
            if not_found:
                response_parts.extend([
                    f"⚠️  Not found ({len(not_found)}):",
                    ", ".join(not_found),
                    ""
                ])
            
            response_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            return [TextContent(
                type="text",
                text="\n".join(response_parts)
            )]
        
        elif name == "get_cv_by_name":
            source = arguments.get("source")
            
            if not source:
                return [TextContent(
                    type="text",
                    text="Error: 'source' parameter is required"
                )]
            
            # Try to read from original JSON file first (more complete)
            cv_file_path = config.DATA_DIR / "cvs" / source
            full_cv_text = None
            cv_name = "Unknown"
            
            if cv_file_path.exists() and cv_file_path.suffix == '.json':
                try:
                    import json
                    with open(cv_file_path, 'r', encoding='utf-8') as f:
                        cv_data = json.load(f)
                    
                    # Extract full text using the indexer's parser
                    full_cv_text, metadata = indexer._parse_cv_file(cv_file_path)
                    cv_name = metadata.get('cv_name', cv_data.get('name', 'Unknown'))
                    
                    # If extracted text is very short, warn about empty CV
                    if len(full_cv_text.strip()) < 100:
                        warning = "\n⚠️  ADVARSEL: Denne CV-en inneholder lite informasjon (kun navn og avdeling)."
                    else:
                        warning = ""
                except Exception as e:
                    logger.warning(f"Failed to read CV file {cv_file_path}: {e}")
                    full_cv_text = None
            
            # Fallback to chunks from ChromaDB if file read failed
            if full_cv_text is None:
                results = indexer.collection.get(
                    where={"source": source}
                )
                
                if not results['documents']:
                    return [TextContent(
                        type="text",
                        text=f"No CV found with source: {source}"
                    )]
                
                # Combine all chunks
                cv_name = results['metadatas'][0].get('cv_name', 'Unknown')
                full_cv_text = "\n\n".join(results['documents'])
                warning = ""
            
            # Check if CV is essentially empty
            if len(full_cv_text.strip()) < 50:
                warning = "\n⚠️  ADVARSEL: Denne CV-en inneholder svært lite informasjon og kan være ufullstendig."
            
            response = f"""CV: {cv_name}
Source: {source}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{warning}

{full_cv_text}
"""
            
            return [TextContent(
                type="text",
                text=response
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error handling tool call: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


def format_search_results(query: str, results: Dict, office_filter: str = None) -> str:
    """
    Format search results into a readable text response
    """
    if not results['documents']:
        filter_info = f" (filtrert på: {office_filter})" if office_filter else ""
        return f"Ingen CV-er funnet for søket: '{query}'{filter_info}\n\nPrøv et annet søk eller sjekk at CV-er er indeksert."
    
    filter_info = f" (filtrert på: {office_filter})" if office_filter else ""
    response_parts = [
        f"Søkeresultater for: '{query}'{filter_info}",
        f"Fant {len(results['documents'])} relevante CV-utdrag",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ""
    ]
    
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'],
        results['metadatas'],
        results.get('distances', [0] * len(results['documents']))
    )):
        cv_name = metadata.get('cv_name', 'Unknown')
        source = metadata.get('source', 'unknown')
        chunk_id = metadata.get('chunk_id', '?')
        total_chunks = metadata.get('total_chunks', '?')
        office = metadata.get('office', '')
        similarity = 1 - distance if distance else 1.0
        
        # Truncate long chunks to save tokens (max 400 chars ≈ 100 words)
        # This prevents Claude Desktop from hitting context limits
        MAX_EXCERPT_LENGTH = 400
        excerpt = doc.strip()
        if len(excerpt) > MAX_EXCERPT_LENGTH:
            excerpt = excerpt[:MAX_EXCERPT_LENGTH] + "..."
        
        office_str = f" | {office}" if office else ""
        
        response_parts.extend([
            f"[{i+1}] {cv_name}{office_str} (Relevans: {similarity:.1%})",
            f"    Kilde: {source} | Chunk {chunk_id}/{total_chunks}",
            "",
            excerpt,
            "",
            "─" * 60,
            ""
        ])
    
    return "\n".join(response_parts)


async def main():
    """
    Main entry point for the MCP server
    """
    logger.info("Starting MCP server for CV-RAG system...")
    
    # Check if index has data
    stats = indexer.get_stats()
    if stats['total_chunks'] == 0:
        logger.warning("No CVs indexed! Please run 'python scripts/index_cvs.py' first")
        print("⚠️  Warning: No CVs indexed yet!", file=sys.stderr)
        print("   Please run: python scripts/index_cvs.py", file=sys.stderr)
    else:
        logger.info(f"Loaded index with {stats['unique_cvs']} CVs ({stats['total_chunks']} chunks)")
    
    # Run the stdio server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP server running on stdio")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import sys
    asyncio.run(main())



