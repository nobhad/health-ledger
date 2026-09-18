#!/usr/bin/env python3
"""
Input validation utilities for API endpoints
"""

from typing import Optional, List, Dict, Any
from flask import jsonify
import re


def validate_gene_symbol(gene_symbol: str) -> tuple[bool, Optional[str]]:
    """
    Validate a gene symbol.
    
    Args:
        gene_symbol: Gene symbol to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if gene_symbol is None:
        return False, "Gene symbol is required"
    
    if not isinstance(gene_symbol, str):
        return False, "Gene symbol must be a string"
    
    if not gene_symbol.strip():
        return False, "Gene symbol is required"
    
    # Gene symbols are typically uppercase alphanumeric with dashes/underscores
    if not re.match(r'^[A-Z0-9_-]+$', gene_symbol.upper()):
        return False, f"Invalid gene symbol format: {gene_symbol}"
    
    if len(gene_symbol) > 20:
        return False, "Gene symbol too long (max 20 characters)"
    
    return True, None


def validate_condition_name(condition: str) -> tuple[bool, Optional[str]]:
    """
    Validate a health condition name.
    
    Args:
        condition: Condition name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not condition:
        return False, "Condition name is required"
    
    if not isinstance(condition, str):
        return False, "Condition name must be a string"
    
    if len(condition) > 200:
        return False, "Condition name too long (max 200 characters)"
    
    # Check for potentially malicious content
    if '<' in condition or '>' in condition:
        return False, "Condition name contains invalid characters"
    
    return True, None


def validate_trait_name(trait: str) -> tuple[bool, Optional[str]]:
    """
    Validate a trait name.
    
    Args:
        trait: Trait name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not trait:
        return False, "Trait name is required"
    
    if not isinstance(trait, str):
        return False, "Trait name must be a string"
    
    if len(trait) > 200:
        return False, "Trait name too long (max 200 characters)"
    
    # Check for potentially malicious content
    if '<' in trait or '>' in trait:
        return False, "Trait name contains invalid characters"
    
    return True, None


def validate_query_params(params: Dict[str, Any], required: List[str] = None, 
                         optional: List[str] = None) -> tuple[bool, Optional[str], Optional[Dict]]:
    """
    Validate query parameters.
    
    Args:
        params: Dictionary of parameters to validate
        required: List of required parameter names
        optional: List of optional parameter names (for type checking)
        
    Returns:
        Tuple of (is_valid, error_message, validated_params)
    """
    if required is None:
        required = []
    if optional is None:
        optional = []
    
    validated = {}
    
    # Check required parameters
    for param in required:
        if param not in params:
            return False, f"Missing required parameter: {param}", None
        if params[param] is None or params[param] == '':
            return False, f"Parameter '{param}' cannot be empty", None
        validated[param] = params[param]
    
    # Validate optional parameters if provided
    for param in optional:
        if param in params and params[param] is not None:
            validated[param] = params[param]
    
    return True, None, validated


def validate_list_param(param_value: Any, param_name: str, max_items: int = 100) -> tuple[bool, Optional[str], Optional[List]]:
    """
    Validate a list parameter (for multiselect queries).
    
    Args:
        param_value: Value to validate
        param_name: Name of the parameter (for error messages)
        max_items: Maximum number of items allowed
        
    Returns:
        Tuple of (is_valid, error_message, validated_list)
    """
    if param_value is None:
        return True, None, []  # Empty list is valid
    
    if isinstance(param_value, str):
        # Single value as string - convert to list
        return True, None, [param_value]
    
    if not isinstance(param_value, list):
        return False, f"{param_name} must be a list or string", None
    
    if len(param_value) > max_items:
        return False, f"{param_name} cannot contain more than {max_items} items", None
    
    # Validate each item is a string
    validated = []
    for item in param_value:
        if not isinstance(item, str):
            return False, f"All items in {param_name} must be strings", None
        if len(item) > 200:
            return False, f"Item in {param_name} too long (max 200 characters)", None
        validated.append(item.strip())
    
    return True, None, validated


def create_error_response(message: str, status_code: int = 400, details: Dict = None) -> tuple:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Tuple of (jsonify response, status_code)
    """
    error_data = {
        'error': message,
        'status': status_code
    }
    
    if details:
        error_data['details'] = details
    
    return jsonify(error_data), status_code

