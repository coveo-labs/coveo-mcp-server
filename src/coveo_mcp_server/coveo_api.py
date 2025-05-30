import os
from typing import Any, Dict, Optional, List
import httpx
import json
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()

# Coveo API constants
COVEO_SEARCH_API_ENDPOINT = "https://{org_id}.org.coveo.com/rest/search/v3?organizationId={org_id}"
COVEO_PASSAGES_API_ENDPOINT = "https://{org_id}.org.coveo.com/rest/search/v3/passages/retrieve?organizationId={org_id}"
COVEO_ANSWER_API_ENDPOINT = "https://{org_id}.org.coveo.com/rest/organizations/{org_id}/answer/v1/configs/{config_id}/generate"
API_KEY = os.getenv("COVEO_API_KEY")
ORG_ID = os.getenv("COVEO_ORGANIZATION_ID")
ANSWER_CONFIG_ID = os.getenv("COVEO_ANSWER_CONFIG_ID", "default")
USER_AGENT = "coveo-mcp-server/1.0"

@dataclass
class SearchContext:
    """Search context for Coveo queries."""
    q: str
    bearer_token: str = field(default_factory=lambda: API_KEY)
    organization_id: str = field(default_factory=lambda: ORG_ID)
    filter: Optional[str] = None
    locale: str = "en-US"
    timezone: str = "America/New_York"
    context: Optional[Dict[str, Any]] = None
    additionalFields: Optional[List[str]] = None


async def make_coveo_request(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Make a request to the Coveo API with proper error handling."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }

    params["organizationId"] = ORG_ID

    endpoint = COVEO_SEARCH_API_ENDPOINT.format(
        org_id=ORG_ID
    )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

async def retrieve_passages(query: str, number_of_passages: int = 5) -> Dict:
    """
    Retrieves passages from Coveo API.
    
    Args:
        query (str): The search query.
        number_of_passages (int): Maximum number of passages to retrieve.
        
    Returns:
        List[Passage]: List of retrieved passages.
    """
    search_context = SearchContext(q=query)
    endpoint = COVEO_PASSAGES_API_ENDPOINT.format(
        org_id=ORG_ID
    )
    
    is_oauth_token = search_context.bearer_token.startswith('x') and not search_context.bearer_token.startswith('xx')

    headers = {
        'Authorization': f'Bearer {search_context.bearer_token}',
        'Content-Type': 'application/json',
        'accept': 'application/json'
    }
    
    # Add organizationId in headers if using API Key
    if not is_oauth_token:
        headers['organizationId'] = search_context.organization_id

    # Only add organizationId as query parameter for OAuth tokens
    params = {}
    if is_oauth_token:
        params['organizationId'] = search_context.organization_id

    payload = {
        "query": search_context.q,
        "filter": search_context.filter,
        "maxPassages": number_of_passages,
        "localization": {
            "locale": search_context.locale,
            "timezone": search_context.timezone
        },
        "context": search_context.context or {},
        "additionalFields": search_context.additionalFields or [],
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(endpoint, headers=headers, json=payload, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            #passages = []
            return data.get('items', [])
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP {e.response.status_code}: {e.response.text}")
            return []
        except Exception as e:
            print(f"Error retrieving passages: {str(e)}")
            return []

async def generate_answer(query: str) -> str:
    """
    Generates an answer using Coveo Answer API's streaming endpoint.
    
    Args:
        query (str): The question to answer.
        
    Returns:
        str: The generated answer or error message.
    """
    if not query:
        return "Error: Query cannot be empty"
    
    # Format the endpoint URL with organization ID and config ID
    endpoint = COVEO_ANSWER_API_ENDPOINT.format(
        org_id=ORG_ID,
        config_id=ANSWER_CONFIG_ID
    )
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Accept-Language': 'en-US',
        'User-Agent': USER_AGENT,
    }
    
    payload = {
        'q': query,
        'context': '',
        'pipelineRuleParameters': {
            'mlGenerativeQuestionAnswering': {
                'responseFormat': {
                    'contentFormat': ['text/markdown', 'text/plain']
                }
            }
        }
    }
    
    try:
        complete_answer = []
        citations = []
        
        async with httpx.AsyncClient() as client:
            async with client.stream('POST', endpoint, headers=headers, json=payload, timeout=60.0) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line.strip() or not line.startswith('data:'):
                        continue
                    
                    # Extract the JSON data part
                    json_data = line.replace('data:', '').strip()
                    try:
                        data = json.loads(json_data)
                        payload_type = data.get('payloadType')
                        
                        # Process different types of responses
                        if payload_type == 'genqa.messageType':
                            payload = json.loads(data.get('payload', '{}'))
                            text_delta = payload.get('textDelta', '')
                            if text_delta:
                                complete_answer.append(text_delta)
                        
                        # Extract citations if available
                        elif payload_type == 'genqa.citationsType':
                            payload = json.loads(data.get('payload', '{}'))
                            citations = payload.get('citations', [])
                        
                        # Check for end of stream or errors
                        elif payload_type == 'genqa.endOfStreamType':
                            break
                        
                    except Exception as e:
                        print(f"Error parsing stream data: {str(e)}")
        
        # Combine answer parts
        answer_text = ''.join(complete_answer)
        
        # Format citations if available
        if citations:
            citation_text = "\n\n**Sources:**\n"
            for i, citation in enumerate(citations):
                title = citation.get('title', 'Untitled')
                click_uri = citation.get('clickUri', '#')
                citation_text += f"{i+1}. [{title}]({click_uri})\n"
            
            answer_text += citation_text
        
        return answer_text
    
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Error generating answer: {str(e)}"
