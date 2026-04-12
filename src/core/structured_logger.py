"""Structured logging with context and lightweight timing helpers."""
import logging
import time
import json
from typing import Optional, Dict, Any
from contextlib import contextmanager
from functools import wraps
import uuid


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter (adds context/performance when provided)."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra context if available
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        if hasattr(record, 'performance'):
            log_data['performance'] = record.performance
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ContextLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context to log records."""
    
    def process(self, msg, kwargs):
        """Add context to log record."""
        extra = kwargs.get('extra', {})
        if 'context' not in extra:
            extra['context'] = {}
        
        # Merge with existing context
        if hasattr(self, 'context'):
            extra['context'].update(self.context)
        
        kwargs['extra'] = extra
        return msg, kwargs


class PerformanceLogger:
    """Logger with performance monitoring capabilities."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._start_times: Dict[str, float] = {}
    
    @contextmanager
    def time_operation(self, operation_name: str, log_level: int = logging.INFO):
        """
        Context manager to time an operation.
        
        Args:
            operation_name: Name of the operation
            log_level: Log level for the timing message
        """
        start_time = time.time()
        operation_id = str(uuid.uuid4())[:8]
        
        try:
            self.logger.log(
                log_level,
                f"Starting operation: {operation_name}",
                extra={'context': {'operation_id': operation_id, 'operation': operation_name}}
            )
            yield operation_id
        finally:
            elapsed_time = time.time() - start_time
            self.logger.log(
                log_level,
                f"Completed operation: {operation_name}",
                extra={
                    'context': {'operation_id': operation_id, 'operation': operation_name},
                    'performance': {'elapsed_seconds': round(elapsed_time, 3)}
                }
            )
    
    def log_performance(self, operation_name: str, elapsed_time: float, 
                       additional_metrics: Optional[Dict[str, Any]] = None):
        """
        Log performance metrics.
        
        Args:
            operation_name: Name of the operation
            elapsed_time: Elapsed time in seconds
            additional_metrics: Additional performance metrics
        """
        metrics = {'elapsed_seconds': round(elapsed_time, 3)}
        if additional_metrics:
            metrics.update(additional_metrics)
        
        self.logger.info(
            f"Performance metrics for {operation_name}",
            extra={'performance': metrics, 'context': {'operation': operation_name}}
        )


def log_execution_time(operation_name: Optional[str] = None):
    """
    Decorator to log function execution time.
    
    Args:
        operation_name: Custom operation name (defaults to function name)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            perf_logger = PerformanceLogger(logger)
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with perf_logger.time_operation(op_name, logging.DEBUG):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def create_structured_logger(
    name: str,
    level: int = logging.INFO,
    use_json: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Create a logger with optional JSON formatting.
    
    Args:
        name: Logger name
        level: Logging level
        use_json: Whether to use JSON formatting
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        from pathlib import Path
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
