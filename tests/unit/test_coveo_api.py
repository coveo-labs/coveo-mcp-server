import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import json
import os
from typing import Dict, Any

import pytest
import httpx

from coveo_mcp_server.coveo_api import (
    make_coveo_request,
    format_search_response,
    format_passage_retrieval_response,
    retrieve_passages,
    generate_answer,
    SearchContext
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


def test_format_search_response():
    """Test formatting of search responses."""
    # Test with complete data
    response = {
        "results": [
            {
                "title": "Test Document",
                "excerpt": "This is a test excerpt",
                "uri": "https://example.com/doc",
                "extra_field": "should be excluded"
            }
        ]
    }
    fields_to_include = ["title", "excerpt", "uri"]
    formatted = format_search_response(response, fields_to_include)
    
    assert "results" in formatted
    assert len(formatted["results"]) == 1
    assert formatted["results"][0]["title"] == "Test Document"
    assert formatted["results"][0]["excerpt"] == "This is a test excerpt"
    assert formatted["results"][0]["uri"] == "https://example.com/doc"
    assert "extra_field" not in formatted["results"][0]

    # Test with missing data
    response = {"results": [{}]}
    formatted = format_search_response(response, fields_to_include)
    assert "results" in formatted
    assert len(formatted["results"]) == 1
    
    # Test with empty response
    response = {}
    formatted = format_search_response(response, fields_to_include)
    assert formatted == {"results": []}


@pytest.mark.asyncio
async def test_make_coveo_request_success():
    """Test successful Coveo API request."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"results": [{"title": "Test Result"}]}
    
    # Mock the AsyncClient as context manager
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call function
        params = {"q": "test query", "numberOfResults": 5, "fieldsToInclude": ["title"]}
        result = await make_coveo_request(params)
        
        # Verify result
        expected = {"results": [{"title": "Test Result"}]}
        assert result == expected


@pytest.mark.asyncio
async def test_make_coveo_request_http_error():
    """Test Coveo API request with HTTP error."""
    # Setup mock response that raises HTTP error
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "HTTP Error", request=MagicMock(), response=MagicMock()
    )
    
    # Mock the AsyncClient as context manager
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call function
        params = {"q": "test query"}
        result = await make_coveo_request(params)
        
        # Verify result contains error
        assert "error" in result


@pytest.mark.asyncio
async def test_make_coveo_request_exception():
    """Test Coveo API request with general exception."""
    # Mock the AsyncClient to raise exception
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("Test exception"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call function
        params = {"q": "test query"}
        result = await make_coveo_request(params)
        
        # Verify result contains error
        assert "error" in result
        assert "Test exception" in result["error"]


@pytest.mark.asyncio
async def test_retrieve_passages_success():
    """Test successful retrieval of passages."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
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
    }
    
    # Mock the AsyncClient as context manager
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    # Patch the global variables and the client
    with patch('coveo_mcp_server.coveo_api.API_KEY', 'mock-api-key'), \
         patch('coveo_mcp_server.coveo_api.ORG_ID', 'mock-org-id'), \
         patch('httpx.AsyncClient', return_value=mock_client):
        
        # Call function
        result = await retrieve_passages("test query")
        
        # Verify result
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["text"] == "This is a test passage"
        assert result[0]["document"]["title"] == "Test Document"
        assert result[0]["document"]["permanentid"] == "test-id"
        assert result[0]["document"]["clickableuri"] == "https://example.com/doc"


@pytest.mark.asyncio
async def test_retrieve_passages_http_error():
    """Test passage retrieval with HTTP error."""
    # Setup mock response that raises HTTP error
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "HTTP Error", request=MagicMock(), response=MagicMock()
    )
    
    # Mock the AsyncClient as context manager
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    # Patch the global variables and the client
    with patch('coveo_mcp_server.coveo_api.API_KEY', 'mock-api-key'), \
         patch('coveo_mcp_server.coveo_api.ORG_ID', 'mock-org-id'), \
         patch('httpx.AsyncClient', return_value=mock_client):
        
        # Call function
        result = await retrieve_passages("test query")
        
        # Verify result is empty list on HTTP error
        assert result == []


@pytest.mark.asyncio
async def test_retrieve_passages_exception():
    """Test passage retrieval with general exception."""
    # Mock the AsyncClient to raise exception
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("Test exception"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    # Patch the global variables and the client
    with patch('coveo_mcp_server.coveo_api.API_KEY', 'mock-api-key'), \
         patch('coveo_mcp_server.coveo_api.ORG_ID', 'mock-org-id'), \
         patch('httpx.AsyncClient', return_value=mock_client):
        
        # Call function
        result = await retrieve_passages("test query")
        
        # Verify result is empty list on exception
        assert result == []


@pytest.mark.asyncio
async def test_generate_answer_success():
    """Test successful answer generation."""
    # Create a proper async context manager mock
    class MockStreamResponse:
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None
        
        def raise_for_status(self):
            pass
        
        async def aiter_lines(self):
            lines = [
                'data:{"payloadType":"genqa.messageType","payload":"{\\"textDelta\\":\\"This is \\"}"}',
                'data:{"payloadType":"genqa.messageType","payload":"{\\"textDelta\\":\\"a test answer\\"}"}',
                'data:{"payloadType":"genqa.citationsType","payload":"{\\"citations\\":[{\\"title\\":\\"Citation Title\\",\\"clickUri\\":\\"https://example.com/citation\\"}]}"}',
                'data:{"payloadType":"genqa.endOfStreamType"}'
            ]
            for line in lines:
                yield line
    
    # Mock the AsyncClient as context manager
    mock_client = AsyncMock()
    mock_client.stream = MagicMock(return_value=MockStreamResponse())
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call function
        result = await generate_answer("test question")
        
        # Verify result
        assert "This is a test answer" in result
        assert "Citation Title" in result
        assert "https://example.com/citation" in result


@pytest.mark.asyncio
async def test_generate_answer_http_error():
    """Test answer generation with HTTP error."""
    # Create a proper async context manager mock that raises HTTPStatusError
    class MockStreamResponse:
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None
        
        def raise_for_status(self):
            response_mock = MagicMock()
            response_mock.status_code = 400
            response_mock.text = "Bad Request"
            raise httpx.HTTPStatusError(
                "HTTP Error", request=MagicMock(), response=response_mock
            )
        
        async def aiter_lines(self):
            # This should not be reached since raise_for_status should raise
            return []
    
    mock_client = AsyncMock()
    mock_client.stream = MagicMock(return_value=MockStreamResponse())
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call function
        result = await generate_answer("test question")
        
        # Verify result contains error
        assert "Error: HTTP 400" in result


@pytest.mark.asyncio
async def test_generate_answer_exception():
    """Test answer generation with general exception."""
    # Mock the AsyncClient to raise exception during stream call
    mock_client = AsyncMock()
    mock_client.stream = MagicMock(side_effect=Exception("Test exception"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call function
        result = await generate_answer("test question")
        
        # Verify result contains error
        assert "Error generating answer: Test exception" in result