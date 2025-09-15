"""
Swagger/OpenAPI parser for the API Testing Agent.

This module handles parsing of Swagger/OpenAPI specification files,
resolving references, and extracting endpoint information.
"""

import json
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class ReferenceResolver:
    """Handles resolution of $ref references in OpenAPI specifications."""
    
    def __init__(self, swagger_data: Dict[str, Any]):
        """
        Initialize reference resolver.
        
        Args:
            swagger_data: The complete Swagger/OpenAPI specification
        """
        self.swagger_data = swagger_data
    
    def resolve_reference(self, ref: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a $ref reference to its actual content.
        
        Args:
            ref: The reference string (e.g., "#/components/schemas/User")
            
        Returns:
            Resolved content or None if reference cannot be resolved
        """
        if not ref.startswith("#/"):
            logger.warning(f"External reference not supported: {ref}")
            return None
        
        try:
            parts = ref.lstrip("#/").split("/")
            node = self.swagger_data
            
            for part in parts:
                if not isinstance(node, dict) or part not in node:
                    logger.warning(f"Reference path not found: {ref}")
                    return None
                node = node[part]
            
            return node
            
        except Exception as e:
            logger.error(f"Error resolving reference {ref}: {e}")
            return None
    
    def resolve_schema_recursively(self, schema: Any, seen_refs: Optional[Set[str]] = None) -> Any:
        """
        Recursively resolve all $ref references in a schema.
        
        Args:
            schema: The schema to resolve
            seen_refs: Set of already seen references to prevent circular references
            
        Returns:
            Schema with all references resolved
        """
        if seen_refs is None:
            seen_refs = set()
        
        if isinstance(schema, dict):
            if "$ref" in schema:
                ref = schema["$ref"]
                
                # Prevent circular references
                if ref in seen_refs:
                    logger.warning(f"Circular reference detected: {ref}")
                    return {"$ref": ref}
                
                seen_refs.add(ref)
                resolved = self.resolve_reference(ref)
                
                if resolved is None:
                    return schema
                
                return self.resolve_schema_recursively(resolved, seen_refs)
            
            # Recursively resolve all values in the dictionary
            return {
                key: self.resolve_schema_recursively(value, seen_refs)
                for key, value in schema.items()
            }
        
        elif isinstance(schema, list):
            # Recursively resolve all items in the list
            return [
                self.resolve_schema_recursively(item, seen_refs)
                for item in schema
            ]
        
        # Return primitive values as-is
        return schema


class SwaggerParser:
    """Parses Swagger/OpenAPI specification files and extracts endpoint information."""
    
    def __init__(self):
        """Initialize Swagger parser."""
        self.reference_resolver = None
    
    def load_swagger_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a Swagger/OpenAPI specification file.
        
        Args:
            file_path: Path to the Swagger/OpenAPI file
            
        Returns:
            Parsed Swagger/OpenAPI data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        try:
            swagger_path = Path(file_path)
            
            if not swagger_path.exists():
                raise FileNotFoundError(f"Swagger file not found: {file_path}")
            
            logger.info(f"Loading Swagger file: {file_path}")
            
            with open(swagger_path, "r", encoding="utf-8") as file:
                swagger_data = json.load(file)
            
            logger.info("Swagger file loaded successfully")
            return swagger_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Swagger file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading Swagger file: {e}")
            raise
    
    def extract_endpoints(self, swagger_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract API endpoints from Swagger/OpenAPI data.
        
        Args:
            swagger_data: Parsed Swagger/OpenAPI data
            
        Returns:
            List of endpoint dictionaries
        """
        logger.info("Extracting endpoints from Swagger specification")
        
        # Initialize reference resolver
        self.reference_resolver = ReferenceResolver(swagger_data)
        
        endpoints = []
        paths = swagger_data.get("paths", {})
        
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            
            for method, details in methods.items():
                # Skip non-HTTP method keys
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
                    continue
                
                try:
                    endpoint = self._extract_single_endpoint(path, method, details, swagger_data)
                    if endpoint:
                        endpoints.append(endpoint)
                        
                except Exception as e:
                    logger.error(f"Error extracting endpoint {method} {path}: {e}")
                    continue
        
        logger.info(f"Extracted {len(endpoints)} endpoints")
        return endpoints
    
    def _extract_single_endpoint(
        self, 
        path: str, 
        method: str, 
        details: Dict[str, Any], 
        swagger_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract a single endpoint from the specification.
        
        Args:
            path: API path
            method: HTTP method
            details: Endpoint details from the specification
            swagger_data: Complete Swagger data for reference resolution
            
        Returns:
            Endpoint dictionary or None if extraction fails
        """
        try:
            # Resolve request body schemas
            resolved_request_body = self._resolve_request_body(details.get("requestBody"))
            
            # Resolve response schemas
            resolved_responses = self._resolve_responses(details.get("responses", {}))
            
            # Resolve parameter schemas
            resolved_parameters = self._resolve_parameters(details.get("parameters", []))
            
            endpoint = {
                "path": path,
                "method": method.upper(),
                "summary": details.get("summary"),
                "description": details.get("description"),
                "tags": details.get("tags", []),
                "operation_id": details.get("operationId"),
                "deprecated": details.get("deprecated", False),
                "consumes": details.get("consumes", []),
                "produces": details.get("produces", []),
                "parameters": resolved_parameters,
                "request_body": resolved_request_body,
                "responses": resolved_responses,
                "security": details.get("security"),
                "examples": details.get("examples"),
                "external_docs": details.get("externalDocs"),
                "x_additional_metadata": {
                    key: value 
                    for key, value in details.items() 
                    if key.startswith("x-")
                }
            }
            
            return endpoint
            
        except Exception as e:
            logger.error(f"Error extracting endpoint {method} {path}: {e}")
            return None
    
    def _resolve_request_body(self, request_body: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Resolve request body schemas.
        
        Args:
            request_body: Request body specification
            
        Returns:
            Resolved request body or None
        """
        if not request_body:
            return None
        
        try:
            resolved_body = request_body.copy()
            content = resolved_body.get("content", {})
            
            for media_type, content_obj in content.items():
                if "schema" in content_obj:
                    content_obj["schema"] = self.reference_resolver.resolve_schema_recursively(
                        content_obj["schema"]
                    )
            
            return resolved_body
            
        except Exception as e:
            logger.error(f"Error resolving request body: {e}")
            return request_body
    
    def _resolve_responses(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve response schemas.
        
        Args:
            responses: Response specifications
            
        Returns:
            Resolved responses
        """
        try:
            resolved_responses = {}
            
            for status_code, response in responses.items():
                resolved_response = response.copy()
                
                # Handle Swagger 2.0 format
                if "schema" in resolved_response:
                    resolved_response["schema"] = self.reference_resolver.resolve_schema_recursively(
                        resolved_response["schema"]
                    )
                
                # Handle OpenAPI 3.x format
                elif "content" in resolved_response:
                    content = resolved_response["content"]
                    for media_type, content_obj in content.items():
                        if "schema" in content_obj:
                            content_obj["schema"] = self.reference_resolver.resolve_schema_recursively(
                                content_obj["schema"]
                            )
                
                resolved_responses[status_code] = resolved_response
            
            return resolved_responses
            
        except Exception as e:
            logger.error(f"Error resolving responses: {e}")
            return responses
    
    def _resolve_parameters(self, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolve parameter schemas.
        
        Args:
            parameters: Parameter specifications
            
        Returns:
            Resolved parameters
        """
        try:
            resolved_parameters = []
            
            for param in parameters:
                resolved_param = param.copy()
                
                if "schema" in resolved_param:
                    resolved_param["schema"] = self.reference_resolver.resolve_schema_recursively(
                        resolved_param["schema"]
                    )
                
                resolved_parameters.append(resolved_param)
            
            return resolved_parameters
            
        except Exception as e:
            logger.error(f"Error resolving parameters: {e}")
            return parameters
    
    def parse_swagger_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a Swagger/OpenAPI file and extract all endpoints.
        
        Args:
            file_path: Path to the Swagger/OpenAPI file
            
        Returns:
            List of extracted endpoint dictionaries
        """
        try:
            swagger_data = self.load_swagger_file(file_path)
            endpoints = self.extract_endpoints(swagger_data)
            return endpoints
            
        except Exception as e:
            logger.error(f"Failed to parse Swagger file {file_path}: {e}")
            raise


# Global parser instance
swagger_parser = SwaggerParser()


def get_swagger_parser() -> SwaggerParser:
    """Get the global Swagger parser instance."""
    return swagger_parser


def parse_swagger_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Convenience function to parse a Swagger file.
    
    Args:
        file_path: Path to the Swagger/OpenAPI file
        
    Returns:
        List of extracted endpoint dictionaries
    """
    return swagger_parser.parse_swagger_file(file_path)
