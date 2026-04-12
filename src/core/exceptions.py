"""
Custom exception classes for better error handling and debugging.
"""
import uuid
from typing import Optional, Dict, Any
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    CONFIGURATION = "configuration"
    DATA_LOAD = "data_load"
    DATA_PROCESS = "data_process"
    DATA_VALIDATION = "data_validation"
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN = "unknown"


class DataIntegrationError(Exception):
    """Base exception for data integration errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        recoverable: bool = False,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize error with enhanced context.
        
        Args:
            message: Error message
            error_code: Unique error code for categorization
            details: Additional error details
            severity: Error severity level
            category: Error category
            recoverable: Whether the error is recoverable
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or f"ERR_{uuid.uuid4().hex[:8].upper()}"
        self.details = details or {}
        self.severity = severity
        self.category = category
        self.recoverable = recoverable
        self.context = context or {}
        self.error_id = str(uuid.uuid4())
    
    def __str__(self) -> str:
        parts = [f"[{self.error_code}] {self.message}"]
        if self.details:
            parts.append(f"Details: {self.details}")
        if self.context:
            parts.append(f"Context: {self.context}")
        return " | ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging."""
        return {
            'error_id': self.error_id,
            'error_code': self.error_code,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'recoverable': self.recoverable,
            'details': self.details,
            'context': self.context
        }


class DataLoadError(DataIntegrationError):
    """Exception raised when data loading fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if file_path:
            context['file_path'] = file_path
        super().__init__(
            message,
            error_code=kwargs.pop('error_code', 'DATA_LOAD_ERROR'),
            category=ErrorCategory.DATA_LOAD,
            context=context,
            **kwargs
        )


class DataProcessError(DataIntegrationError):
    """Exception raised when data processing fails."""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if operation:
            context['operation'] = operation
        super().__init__(
            message,
            error_code=kwargs.pop('error_code', 'DATA_PROCESS_ERROR'),
            category=ErrorCategory.DATA_PROCESS,
            context=context,
            **kwargs
        )


class APIClientError(DataIntegrationError):
    """Exception raised when API client operations fail."""
    
    def __init__(
        self,
        message: str,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        retryable: bool = False,
        **kwargs
    ):
        context = kwargs.pop('context', {})
        if endpoint:
            context['endpoint'] = endpoint
        if status_code:
            context['status_code'] = status_code
        super().__init__(
            message,
            error_code=kwargs.pop('error_code', 'API_CLIENT_ERROR'),
            category=ErrorCategory.API_ERROR,
            recoverable=retryable,
            context=context,
            **kwargs
        )


class NetworkError(APIClientError):
    """Exception raised for network-related errors."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            endpoint=endpoint,
            error_code=kwargs.pop('error_code', 'NETWORK_ERROR'),
            category=ErrorCategory.NETWORK_ERROR,
            retryable=True,
            **kwargs
        )


class TimeoutError(APIClientError):
    """Exception raised for timeout errors."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, timeout: Optional[float] = None, **kwargs):
        context = kwargs.pop('context', {})
        if timeout:
            context['timeout_seconds'] = timeout
        super().__init__(
            message,
            endpoint=endpoint,
            error_code=kwargs.pop('error_code', 'TIMEOUT_ERROR'),
            category=ErrorCategory.TIMEOUT_ERROR,
            retryable=True,
            context=context,
            **kwargs
        )


class ConfigurationError(DataIntegrationError):
    """Exception raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if config_key:
            context['config_key'] = config_key
        super().__init__(
            message,
            error_code=kwargs.pop('error_code', 'CONFIGURATION_ERROR'),
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            context=context,
            **kwargs
        )


class ValidationError(DataIntegrationError):
    """Exception raised when data validation fails."""
    
    def __init__(self, message: str, validation_rule: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if validation_rule:
            context['validation_rule'] = validation_rule
        super().__init__(
            message,
            error_code=kwargs.pop('error_code', 'VALIDATION_ERROR'),
            category=ErrorCategory.DATA_VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            context=context,
            **kwargs
        )


class ResourceError(DataIntegrationError):
    """Exception raised when resource limits are exceeded."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, **kwargs):
        context = kwargs.pop('context', {})
        if resource_type:
            context['resource_type'] = resource_type
        super().__init__(
            message,
            error_code=kwargs.pop('error_code', 'RESOURCE_ERROR'),
            category=ErrorCategory.RESOURCE_ERROR,
            severity=ErrorSeverity.HIGH,
            context=context,
            **kwargs
        )
