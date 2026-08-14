"""
Utility helper functions for the AI Test Automation Engine.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def ensure_directory_exists(directory: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Path to the directory
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def load_config_from_env(prefix: str = "") -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Args:
        prefix: Optional prefix for environment variables
        
    Returns:
        Dictionary of configuration values
    """
    config = {}
    for key, value in os.environ.items():
        if prefix and not key.startswith(prefix):
            continue
        config[key.lower().replace(prefix.lower(), "")] = value
    return config


def safe_get_dict_value(dictionary: Dict, key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary with dot notation support.
    
    Args:
        dictionary: Dictionary to query
        key: Key to retrieve (supports dot notation like 'parent.child')
        default: Default value if key not found
        
    Returns:
        Value from dictionary or default
    """
    keys = key.split(".")
    current = dictionary
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current


def format_log_message(level: str, message: str, **kwargs) -> str:
    """
    Format a log message with additional context.
    
    Args:
        level: Log level (INFO, WARNING, ERROR, etc.)
        message: Base message
        **kwargs: Additional context to include
        
    Returns:
        Formatted log message
    """
    if not kwargs:
        return message
    
    context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    return f"{message} [{context}]"


def retry_operation(func, max_attempts: int = 3, delay: float = 1.0) -> Any:
    """
    Retry an operation with exponential backoff.
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries (in seconds)
        
    Returns:
        Result from the function
        
    Raises:
        Exception: Last exception from the function
    """
    import time
    
    last_exception = None
    current_delay = delay
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_attempts:
                logger.warning(
                    f"Attempt {attempt} failed, retrying in {current_delay}s: {e}"
                )
                time.sleep(current_delay)
                current_delay *= 2
    
    raise last_exception


def parse_test_parameters(params: str) -> Dict[str, Any]:
    """
    Parse test parameters from a string format.
    
    Args:
        params: Parameter string (e.g., "key1=value1,key2=value2")
        
    Returns:
        Dictionary of parsed parameters
    """
    result = {}
    if not params:
        return result
    
    for param in params.split(","):
        if "=" in param:
            key, value = param.split("=", 1)
            result[key.strip()] = value.strip()
    
    return result
