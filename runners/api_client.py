"""
API client for the API Testing Agent.

This module provides functionality for making HTTP requests to API endpoints
and handling responses.
"""

import requests
from typing import Dict, Any, Optional, Union
from config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


class APIResponse:
    """Represents an API response with status, headers, and data."""
    
    def __init__(
        self,
        status_code: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        error: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ):
        """
        Initialize API response.
        
        Args:
            status_code: HTTP status code
            headers: Response headers
            data: Response data (JSON or text)
            error: Error message if request failed
            execution_time_ms: Request execution time in milliseconds
        """
        self.status_code = status_code
        self.headers = headers or {}
        self.data = data
        self.error = error
        self.execution_time_ms = execution_time_ms
        self.success = status_code is not None and 200 <= status_code < 300
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert response to dictionary.
        
        Returns:
            Dictionary representation of the response
        """
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "success": self.success
        }


class APIClient:
    """HTTP client for making API requests."""
    
    def __init__(self):
        """Initialize API client."""
        self.config = get_config()
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'API-Testing-Agent/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """
        Make an HTTP request to the specified URL.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            url: Full API URL
            headers: Request headers
            query_params: Query string parameters
            payload: Request body (for POST/PUT/PATCH)
            timeout: Request timeout in seconds
            
        Returns:
            APIResponse object containing the response details
        """
        method = method.upper()
        timeout = timeout or self.config.api.timeout
        
        print(f"🌐 [API_CLIENT] Making {method} request to {url}")
        print(f"📤 [API_CLIENT] Headers: {headers}")
        print(f"📤 [API_CLIENT] Query params: {query_params}")
        print(f"📤 [API_CLIENT] Payload: {payload}")
        logger.info(f"Making {method} request to {url}")
        
        try:
            # Prepare request parameters
            request_kwargs = {
                'method': method,
                'url': url,
                'timeout': timeout
            }
            
            if headers:
                request_kwargs['headers'] = headers
            
            if query_params:
                request_kwargs['params'] = query_params
            
            if payload and method in ['POST', 'PUT', 'PATCH']:
                request_kwargs['json'] = payload
            
            # Make the request with retries on connection errors/timeouts
            import time
            start_time = time.time()
            
            retries = getattr(self.config.api, 'max_retries', 3) or 0
            attempt = 0
            last_error: Optional[str] = None
            backoff_seconds = 0.5
            response = None
            
            while True:
                try:
                    print("⏳ [API_CLIENT] Sending request...")
                    response = self.session.request(**request_kwargs)
                    break
                except requests.exceptions.Timeout:
                    last_error = f"Request timeout after {timeout} seconds"
                except requests.exceptions.ConnectionError:
                    last_error = "Connection error - unable to reach the server"
                except requests.exceptions.RequestException as e:
                    last_error = f"Request failed: {str(e)}"
                    # Non-retryable by default; break
                    break
                
                if attempt >= retries:
                    break
                attempt += 1
                print(f"🔁 [API_CLIENT] Retry {attempt}/{retries} after error: {last_error}")
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 5)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            if response is None:
                return APIResponse(error=last_error)
            
            # Parse response data
            try:
                response_data = response.json()
                print(f"📥 [API_CLIENT] Response parsed as JSON")
            except ValueError:
                response_data = response.text
                print(f"📥 [API_CLIENT] Response parsed as text")
            
            api_response = APIResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                data=response_data,
                execution_time_ms=execution_time_ms
            )
            
            print(f"✅ [API_CLIENT] Request completed: {response.status_code} in {execution_time_ms}ms")
            logger.info(f"Request completed: {response.status_code} in {execution_time_ms}ms")
            return api_response
            
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {timeout} seconds"
            logger.error(error_msg)
            return APIResponse(error=error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error - unable to reach the server"
            logger.error(error_msg)
            return APIResponse(error=error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return APIResponse(error=error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return APIResponse(error=error_msg)

    def check_connectivity(self, base_url: str, retries: Optional[int] = None) -> bool:
        """Check if the API server is reachable with lightweight GET/HEAD and retries."""
        import time
        tries = retries if retries is not None else getattr(self.config.api, 'max_retries', 3)
        if tries is None:
            tries = 0
        backoff_seconds = 0.5
        for attempt in range(tries + 1):
            try:
                # Prefer HEAD; fall back to GET if not allowed
                resp = self.session.request('HEAD', base_url, timeout=self.config.api.timeout)
                if resp.status_code < 500:
                    return True
            except Exception:
                pass
            try:
                resp = self.session.request('GET', base_url, timeout=self.config.api.timeout)
                if resp.status_code < 500:
                    return True
            except Exception:
                pass
            if attempt < tries:
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 5)
        return False
    
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """
        Make a GET request.
        
        Args:
            url: Request URL
            headers: Request headers
            query_params: Query parameters
            timeout: Request timeout
            
        Returns:
            APIResponse object
        """
        return self.make_request('GET', url, headers, query_params, timeout=timeout)
    
    def post(
        self,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """
        Make a POST request.
        
        Args:
            url: Request URL
            payload: Request body
            headers: Request headers
            query_params: Query parameters
            timeout: Request timeout
            
        Returns:
            APIResponse object
        """
        return self.make_request('POST', url, headers, query_params, payload, timeout)
    
    def put(
        self,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """
        Make a PUT request.
        
        Args:
            url: Request URL
            payload: Request body
            headers: Request headers
            query_params: Query parameters
            timeout: Request timeout
            
        Returns:
            APIResponse object
        """
        return self.make_request('PUT', url, headers, query_params, payload, timeout)
    
    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """
        Make a DELETE request.
        
        Args:
            url: Request URL
            headers: Request headers
            query_params: Query parameters
            timeout: Request timeout
            
        Returns:
            APIResponse object
        """
        return self.make_request('DELETE', url, headers, query_params, timeout=timeout)
    
    def patch(
        self,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """
        Make a PATCH request.
        
        Args:
            url: Request URL
            payload: Request body
            headers: Request headers
            query_params: Query parameters
            timeout: Request timeout
            
        Returns:
            APIResponse object
        """
        return self.make_request('PATCH', url, headers, query_params, payload, timeout)
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.info("API client session closed")


# Global API client instance
api_client = APIClient()


def get_api_client() -> APIClient:
    """Get the global API client instance."""
    return api_client


def make_api_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None
) -> APIResponse:
    """
    Convenience function to make an API request.
    
    Args:
        method: HTTP method
        url: Request URL
        headers: Request headers
        query_params: Query parameters
        payload: Request body
        timeout: Request timeout
        
    Returns:
        APIResponse object
    """
    return api_client.make_request(method, url, headers, query_params, payload, timeout)
