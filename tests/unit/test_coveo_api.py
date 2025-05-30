import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import json
import os
from typing import Dict, Any

import pytest
import httpx

from coveo_mcp_server.coveo_api import (
    make_coveo_request,
    format_search_result,
    retrieve_passages,
    generate_answer,
    Passage
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


def test_format_search_result():
    """Test formatting of search results."""
    # Test with complete data
    result = {
        "title": "Test Document",
        "excerpt": "This is a test excerpt",
        "uri": "https://example.com/doc"
    }
    formatted = format_search_result(result)
    assert "Test Document" in formatted
    assert "This is a test excerpt" in formatted
    assert "https://example.com/doc" in formatted

    # Test with missing data
    result = {}
    formatted = format_search_result(result)
    assert "Untitled" in formatted
    assert "No excerpt available" in formatted
    assert "No URI available" in formatted


@pytest.mark.asyncio
async def test_make_coveo_request_success():
    """Test successful Coveo API request."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"results": [{"title": "Test Result"}]}
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        # Call function
        params = {"q": "test query", "numberOfResults": 5}
        result = await make_coveo_request(params)

        # Verify result
        assert result == {"results": [{"title": "Test Result"}]}


@pytest.mark.asyncio
async def test_make_coveo_request_http_error():
    """Test Coveo API request with HTTP error."""
    # Setup mock response for HTTP error
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        # Call function
        params = {"q": "test query"}
        result = await make_coveo_request(params)

        # Verify result contains error
        assert "error" in result


@pytest.mark.asyncio
async def test_make_coveo_request_exception():
    """Test Coveo API request with general exception."""
    # Setup mock to raise exception
    with patch('httpx.AsyncClient.get', side_effect=Exception("Test exception")):
        # Call function
        params = {"q": "test query"}
        result = await make_coveo_request(params)

        # Verify result contains error
        assert "error" in result
        assert "Test exception" in result["error"]


@pytest.mark.asyncio
async def test_retrieve_passages_success():
    """Test successful retrieval of passages."""
    # Setup mock response with a synchronous json method to avoid coroutine issues
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "items": [
            {
                "text": "This is a test passage",
                "relevanceScore": 0.95,
                "document": {
                    "title": "Test Document",
                    "permanentid": "test-id",
                    "clickableuri": "https://example.com/doc"
                }
            }
        ]
    })
    
    # Use AsyncMock for the post function
    mock_post = AsyncMock(return_value=mock_response)
    
    with patch('httpx.AsyncClient.post', mock_post):
        # Call function
        result = await retrieve_passages("test query")

        # Verify result
        assert len(result) == 1
        assert isinstance(result[0], Passage)
        assert result[0].text == "This is a test passage"
        assert result[0].relevance_score == 0.95
        assert result[0].document_title == "Test Document"


@pytest.mark.asyncio
async def test_retrieve_passages_http_error():
    """Test passage retrieval with HTTP error."""
    # Setup mock to raise HTTP error
    with patch('httpx.AsyncClient.post', side_effect=httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )):
        # Call function
        result = await retrieve_passages("test query")

        # Verify empty result on error
        assert result == []


@pytest.mark.asyncio
async def test_retrieve_passages_exception():
    """Test passage retrieval with general exception."""
    # Setup mock to raise exception
    with patch('httpx.AsyncClient.post', side_effect=Exception("Test exception")):
        # Call function
        result = await retrieve_passages("test query")

        # Verify empty result on error
        assert result == []


@pytest.mark.asyncio
async def test_generate_answer_success():
    """Test successful answer generation."""
    # Setup mock for streaming response
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    
    # Mock the streaming lines with AsyncMock
    lines = [
        'data:{"payloadType":"genqa.messageType","payload":"{\\"textDelta\\":\\"This is part 1\\"}"}',
        'data:{"payloadType":"genqa.messageType","payload":"{\\"textDelta\\":\\" of the answer\\"}"}',
        'data:{"payloadType":"genqa.citationsType","payload":"{\\"citations\\":[{\\"title\\":\\"Test Source\\",\\"clickUri\\":\\"https://example.com\\"}]}"}',
        'data:{"payloadType":"genqa.endOfStreamType"}'
    ]
    
    # Create a proper async iterator
    async def mock_aiter_lines():
        for line in lines:
            yield line
    
    mock_response.aiter_lines = mock_aiter_lines
    
    mock_stream = AsyncMock()
    mock_stream.__aenter__.return_value = mock_response
    
    with patch('httpx.AsyncClient.stream', return_value=mock_stream):
        # Call function
        result = await generate_answer("test question")

        # Verify result
        assert "This is part 1 of the answer" in result
        assert "Sources" in result
        assert "Test Source" in result


@pytest.mark.asyncio
async def test_generate_answer_http_error():
    """Test answer generation with HTTP error."""
    # Create a proper mock response for HTTP error
    mock_request = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    
    http_error = httpx.HTTPStatusError("HTTP Error", request=mock_request, response=mock_response)
    
    # Patch the client.stream method to raise the error
    with patch('httpx.AsyncClient.stream') as mock_stream:
        # Make the __aenter__ method raise the HTTP error
        mock_stream.side_effect = http_error
        
        # Call function
        result = await generate_answer("test question")
        
        # Verify error message matches what's in the generate_answer function
        assert "Error: HTTP 400: Bad Request" in result


@pytest.mark.asyncio
async def test_generate_answer_exception():
    """Test answer generation with general exception."""
    # Setup mock to raise exception
    with patch('httpx.AsyncClient.stream', side_effect=Exception("Test exception")):
        # Call function
        result = await generate_answer("test question")

        # Verify error message
        assert "Error generating answer:" in result