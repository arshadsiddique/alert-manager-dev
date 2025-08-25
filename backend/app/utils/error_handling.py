import logging
import traceback
import time
from typing import Any, Dict, Optional, Callable
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

class AlertMatchingError(Exception):
    """Custom exception for alert matching errors."""
    pass

class JSMAPIError(Exception):
    """Custom exception for JSM API errors."""
    pass

class GrafanaAPIError(Exception):
    """Custom exception for Grafana API errors."""
    pass

class DataExtractionError(Exception):
    """Custom exception for data extraction errors."""
    pass

def handle_extraction_errors(default_return=None):
    """Decorator for handling data extraction errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_logger = logging.getLogger(func.__module__)
                func_logger.error(f"Error in {func.__name__}: {e}")
                func_logger.debug(f"Traceback: {traceback.format_exc()}")
                return default_return
        return wrapper
    return decorator

def handle_api_errors(max_retries: int = 3, retry_delay: float = 1.0):
    """Decorator for handling API errors with retry logic."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (JSMAPIError, GrafanaAPIError) as e:
                    last_exception = e
                    func_logger = logging.getLogger(func.__module__)
                    
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        func_logger.warning(
                            f"API error in {func.__name__} (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        func_logger.error(f"API error in {func.__name__} after {max_retries} attempts: {e}")
                except Exception as e:
                    # Non-API errors should not be retried
                    func_logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    func_logger.debug(f"Traceback: {traceback.format_exc()}")
                    raise
            
            # If we get here, all retries failed
            raise last_exception
        return wrapper
    return decorator

def validate_alert_data(alert_data: Dict[str, Any], source: str) -> bool:
    """
    Validate alert data structure.
    
    Args:
        alert_data: The alert data to validate
        source: Either 'grafana' or 'jsm'
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(alert_data, dict):
        logger.warning(f"Alert data is not a dictionary: {type(alert_data)}")
        return False
    
    required_fields = {
        'grafana': ['labels'],
        'jsm': ['message']
    }
    
    if source not in required_fields:
        logger.warning(f"Unknown source '{source}', expected 'grafana' or 'jsm'")
        return False
    
    # For JSM alerts, check if data is nested
    if source == 'jsm':
        # Check if it's a nested structure
        if 'data' in alert_data:
            alert_data = alert_data['data']
    
    missing_fields = []
    for field in required_fields[source]:
        if field not in alert_data:
            missing_fields.append(field)
    
    if missing_fields:
        logger.warning(f"Missing required fields in {source} alert: {missing_fields}")
        return False
    
    return True

def safe_dict_get(data: Dict, *keys, default=None):
    """
    Safely get nested dictionary values.
    
    Args:
        data: The dictionary to search
        *keys: The nested keys to follow
        default: Default value if key path doesn't exist
    
    Returns:
        The value at the key path, or default if not found
    """
    try:
        result = data
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return default
        return result
    except Exception:
        return default

def log_performance(func_name: str, start_time: float, details: Dict = None):
    """Log performance metrics for a function."""
    end_time = time.time()
    duration = end_time - start_time
    
    log_data = {
        'function': func_name,
        'duration_seconds': round(duration, 3),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        log_data.update(details)
    
    if duration > 5.0:  # Log slow operations
        logger.warning(f"Slow operation: {log_data}")
    else:
        logger.debug(f"Performance: {log_data}")

class ErrorContext:
    """Context manager for enhanced error handling and logging."""
    
    def __init__(self, operation_name: str, logger_instance: logging.Logger = None):
        self.operation_name = operation_name
        self.logger = logger_instance or logger
        self.start_time = None
        self.errors = []
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.debug(f"Operation '{self.operation_name}' completed successfully in {duration:.3f}s")
        else:
            self.logger.error(
                f"Operation '{self.operation_name}' failed after {duration:.3f}s: "
                f"{exc_type.__name__}: {exc_val}"
            )
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Return False to propagate exceptions
        return False
    
    def add_warning(self, message: str, details: Dict = None):
        """Add a warning to the error context."""
        warning_data = {'message': message, 'timestamp': datetime.utcnow().isoformat()}
        if details:
            warning_data.update(details)
        
        self.errors.append(warning_data)
        self.logger.warning(f"[{self.operation_name}] {message}")
    
    def add_error(self, message: str, exception: Exception = None, details: Dict = None):
        """Add an error to the error context."""
        error_data = {
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'error'
        }
        
        if exception:
            error_data['exception'] = str(exception)
            error_data['exception_type'] = type(exception).__name__
        
        if details:
            error_data.update(details)
        
        self.errors.append(error_data)
        self.logger.error(f"[{self.operation_name}] {message}")

def create_error_summary(errors: list, operation: str) -> Dict:
    """Create a summary of errors for reporting."""
    if not errors:
        return {'status': 'success', 'operation': operation}
    
    error_counts = {}
    warnings = []
    errors_list = []
    
    for error in errors:
        level = error.get('level', 'warning')
        error_counts[level] = error_counts.get(level, 0) + 1
        
        if level == 'error':
            errors_list.append(error)
        else:
            warnings.append(error)
    
    return {
        'status': 'error' if errors_list else 'warning',
        'operation': operation,
        'summary': error_counts,
        'errors': errors_list,
        'warnings': warnings,
        'total_issues': len(errors)
    }

# Monitoring and metrics collection
class OperationMetrics:
    """Collect and track operation metrics."""
    
    def __init__(self):
        self.operations = {}
        self.start_time = time.time()
    
    def record_operation(self, operation: str, duration: float, success: bool, details: Dict = None):
        """Record an operation metric."""
        if operation not in self.operations:
            self.operations[operation] = {
                'count': 0,
                'success_count': 0,
                'total_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0,
                'errors': []
            }
        
        op_data = self.operations[operation]
        op_data['count'] += 1
        op_data['total_duration'] += duration
        op_data['min_duration'] = min(op_data['min_duration'], duration)
        op_data['max_duration'] = max(op_data['max_duration'], duration)
        
        if success:
            op_data['success_count'] += 1
        else:
            error_info = {
                'timestamp': datetime.utcnow().isoformat(),
                'duration': duration
            }
            if details:
                error_info.update(details)
            op_data['errors'].append(error_info)
    
    def get_summary(self) -> Dict:
        """Get a summary of all recorded metrics."""
        summary = {
            'collection_duration': time.time() - self.start_time,
            'operations': {}
        }
        
        for op_name, op_data in self.operations.items():
            if op_data['count'] > 0:
                summary['operations'][op_name] = {
                    'total_calls': op_data['count'],
                    'success_rate': op_data['success_count'] / op_data['count'],
                    'average_duration': op_data['total_duration'] / op_data['count'],
                    'min_duration': op_data['min_duration'],
                    'max_duration': op_data['max_duration'],
                    'error_count': len(op_data['errors'])
                }
        
        return summary
    
    def log_summary(self, logger_instance: logging.Logger = None):
        """Log the metrics summary."""
        summary = self.get_summary()
        log_instance = logger_instance or logger
        
        log_instance.info(f"Operation metrics summary: {summary}")
        
        # Log individual operation details
        for op_name, op_metrics in summary['operations'].items():
            if op_metrics['error_count'] > 0:
                log_instance.warning(
                    f"Operation '{op_name}': {op_metrics['error_count']} errors out of "
                    f"{op_metrics['total_calls']} calls (success rate: {op_metrics['success_rate']:.2%})"
                )

# Global metrics instance
global_metrics = OperationMetrics()