import json
from typing import Any, Dict
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from coveo_mcp_server.coveo_api import make_coveo_request, retrieve_passages, generate_answer

load_dotenv()

mcp = FastMCP("coveo_mcp_server")

@mcp.tool()
async def search_coveo(query: str, numberOfResults: int = 5) -> Dict[str, Any]:
    """
    Use search_coveo when the goal is to retrieve metadata, titles, or URLs related to documents.
    Ideal for exploring information broadly, navigating multiple sources, or presenting lists of content without needing the content itself.

    Args:

        query (str): The search query.

        numberOfResults (int, optional): How many results to retrieve. Default: 5.

    Returns:

        str: JSON Formatted search results or an error message.
    """

    payload = {
        "q": query,
        "numberOfResults": numberOfResults,
        "fieldsToExclude": [
            "rankingInfo"
        ],
        "fieldsToInclude": [
            "title",
            "uri",
            "excerpt",
            "printableUri",
            "clickUri"
        ],
        "excerptLength": 500,
        "debugRankingInformation": False
    }

    data = await make_coveo_request(payload)
    
    if data and "error" not in data:
        if "results" in data and data["results"]:
            return  json.dumps(data["results"])
        return "No results found for this query."
    return f"Error: {data.get('error', 'Unknown error occurred')}"


@mcp.tool()
async def passage_retrieval(query: str, numberOfPassages: int = 5) -> Dict[str, Any]:
    """
    Use passage_retrieval to extract highly relevant text snippets from documents.
    Useful when building answers, summaries, or even new documents from source material.
    Choose this tool when you need accurate, content-rich inputs to support generation beyond what a single answer can provide.
    
    Args:
        query (str): The search query.

        numberOfPassages (int, optional): How many passages to retrieve. Default: 5. Maximum: 20.
        
    Returns:
        str: JSON Formatted passages or error message.
    """
    if not query:
        return "Error: Query cannot be empty"
    
    try:
        passages = await retrieve_passages(query=query, number_of_passages=numberOfPassages)
        
        if not passages:
            return "No passages found for this query."
        
        return json.dumps(passages)
    except Exception as e:
        return f"Error retrieving passages: {str(e)}"


@mcp.tool()
async def answer_question(query: str) -> str:
    """
    Use answer_question when the query requires a complete, consistent, and well-structured answer.
    This tool uses a prompt-engineered LLM, combining passages and documents, with safeguards to reduce hallucinations, ensure factual accuracy, and enforce security constraints.
    Designed for delivering clear, direct answers that are ready to consume.
    
    Args:
        query (str): The question to answer.
        
    Returns:
        str: The generated answer with citations or error message.
    """
    if not query:
        return "Error: Query cannot be empty"
    
    try:
        return await generate_answer(query)
    except Exception as e:
        return f"Error generating answer: {str(e)}"