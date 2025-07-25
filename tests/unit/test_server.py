import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import os

import pytest

from coveo_mcp_server.server import (
    search_coveo,
    passage_retrieval,
    answer_question,
    customer_service_agent
)


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Fixture to mock environment variables for all tests."""
    with patch.dict(os.environ, {
        "COVEO_API_KEY": "mock-api-key",
        "COVEO_ORGANIZATION_ID": "mock-org-id",
        "COVEO_ANSWER_CONFIG_ID": "mock-config-id"
    }):
        yield


@pytest.mark.asyncio
async def test_search_coveo_success():
    """Test successful search."""
    # Setup mock response
    mock_make_request = AsyncMock()
    mock_make_request.return_value = {
        "results": [
            {
                "title": "Test Document",
                "excerpt": "This is a test excerpt",
                "uri": "https://example.com/doc"
            }
        ]
    }
    
    with patch('coveo_mcp_server.server.make_coveo_request', mock_make_request):
        # Call function
        result = await search_coveo("test query", numberOfResults=5)

        # Verify result
        assert "Test Document" in result
        assert "This is a test excerpt" in result
        mock_make_request.assert_called_once()
        call_args = mock_make_request.call_args.args[0]
        assert call_args["q"] == "test query"
        assert call_args["numberOfResults"] == 5


@pytest.mark.asyncio
async def test_search_coveo_empty_results():
    """Test search with empty results."""
    # Setup mock response
    mock_make_request = AsyncMock()
    mock_make_request.return_value = {"results": []}
    
    with patch('coveo_mcp_server.server.make_coveo_request', mock_make_request):
        # Call function
        result = await search_coveo("test query")

        # Verify result
        assert result == "No results found for this query."


@pytest.mark.asyncio
async def test_search_coveo_error():
    """Test search with error."""
    # Setup mock response
    mock_make_request = AsyncMock()
    mock_make_request.return_value = {"error": "API error"}
    
    with patch('coveo_mcp_server.server.make_coveo_request', mock_make_request):
        # Call function
        result = await search_coveo("test query")

        # Verify result
        assert "Error:" in result
        assert "API error" in result


@pytest.mark.asyncio
async def test_passage_retrieval_success():
    """Test successful passage retrieval."""
    # Create mock passages
    mock_passage = MagicMock()
    mock_passage.format.return_value = "Formatted passage text"
    mock_retrieve_passages = AsyncMock()
    mock_retrieve_passages.return_value = [mock_passage]
    
    with patch('coveo_mcp_server.server.retrieve_passages', mock_retrieve_passages):
        # Call function
        result = await passage_retrieval("test query")

        # Verify result
        assert result == "Formatted passage text"
        mock_retrieve_passages.assert_called_once_with("test query")


@pytest.mark.asyncio
async def test_passage_retrieval_empty():
    """Test passage retrieval with no results."""
    # Setup mock to return empty list
    mock_retrieve_passages = AsyncMock()
    mock_retrieve_passages.return_value = []
    
    with patch('coveo_mcp_server.server.retrieve_passages', mock_retrieve_passages):
        # Call function
        result = await passage_retrieval("test query")

        # Verify result
        assert result == "No passages found for this query."


@pytest.mark.asyncio
async def test_passage_retrieval_exception():
    """Test passage retrieval with exception."""
    # Setup mock to raise exception
    mock_retrieve_passages = AsyncMock()
    mock_retrieve_passages.side_effect = Exception("Test exception")
    
    with patch('coveo_mcp_server.server.retrieve_passages', mock_retrieve_passages):
        # Call function
        result = await passage_retrieval("test query")

        # Verify result
        assert "Error retrieving passages:" in result
        assert "Test exception" in result


@pytest.mark.asyncio
async def test_answer_question_success():
    """Test successful answer generation."""
    # Setup mock response
    mock_generate_answer = AsyncMock()
    mock_generate_answer.return_value = "This is the answer."
    
    with patch('coveo_mcp_server.server.generate_answer', mock_generate_answer):
        # Call function
        result = await answer_question("test question")

        # Verify result
        assert result == "This is the answer."
        mock_generate_answer.assert_called_once_with("test question")


@pytest.mark.asyncio
async def test_answer_question_exception():
    """Test answer generation with exception."""
    # Setup mock to raise exception
    mock_generate_answer = AsyncMock()
    mock_generate_answer.side_effect = Exception("Test exception")
    
    with patch('coveo_mcp_server.server.generate_answer', mock_generate_answer):
        # Call function
        result = await answer_question("test question")

        # Verify result
        assert "Error generating answer:" in result
        assert "Test exception" in result

@pytest.mark.asyncio
async def test_empty_queries():
    """Test all tools with empty queries."""
    # Test passage_retrieval with empty query
    result = await passage_retrieval("")
    assert result == "Error: Query cannot be empty"

    # Test answer_question with empty query
    result = await answer_question("")
    assert result == "Error: Query cannot be empty"