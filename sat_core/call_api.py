from typing import Dict, Any, Optional
import requests
import sys
import os

# Add parent directory to path to import console logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from console_logger import log_to_console


def call_api(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
    test_description: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    method = method.upper()
    
    # Log API details to console
    log_to_console(f"*****test_description : {test_description} *****", "test")
    log_to_console(f"method : {method}", "api")
    log_to_console(f"url : {url}", "api")
    log_to_console(f"headers : {headers}", "api")
    log_to_console(f"payload : {payload}", "api")

    try:
        response = requests.request(
            method=method, url=url, headers=headers, params=query_params, json=payload, timeout=timeout
        )
        
        # Log response details
        log_to_console(f"status_code : {response.status_code}", "response")
        try:
            data = response.json()
            log_to_console(f"response_data : {data}", "response")
        except ValueError:
            data = response.text
            log_to_console(f"response_data : {data}", "response")
            
        return {"status_code": response.status_code, "headers": dict(response.headers), "data": data}
    except requests.exceptions.RequestException as e:
        log_to_console(f"api error : {str(e)}", "error")
        return {"status_code": None, "error": str(e)}
