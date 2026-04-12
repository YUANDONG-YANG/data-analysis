"""Logging setup with structured context/performance fields."""
import logging
import sys
from typing import Optional
from pathlib import Path
from .config import LoggingConfig


class LoggerFactory:
    """Factory for creating configured loggers."""
    
    @staticmethod
    def create_logger(name: str, config: LoggingConfig, 
                     log_file: Optional[Path] = None) -> logging.Logger:
        """
        Create and configure a logger.
        
        Args:
            name: Logger name
            config: Logging configuration
            log_file: Optional log file path
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, config.level.upper()))
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Console handler with enhanced formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.level.upper()))
        
        # Enhanced formatter that includes context and performance data
        class EnhancedFormatter(logging.Formatter):
            def format(self, record):
                # Base format
                msg = super().format(record)
                
                # Add context if available
                if hasattr(record, 'context') and record.context:
                    context_str = ' | '.join([f"{k}={v}" for k, v in record.context.items() if k not in ['pipeline_id', 'step']])
                    if context_str:
                        msg += f" | Context: {context_str}"
                
                # Add performance if available
                if hasattr(record, 'performance') and record.performance:
                    perf_str = ' | '.join([f"{k}={v}" for k, v in record.performance.items()])
                    if perf_str:
                        msg += f" | Performance: {perf_str}"
                
                return msg
        
        console_formatter = EnhancedFormatter(
            '%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt=config.datefmt
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, config.level.upper()))
            file_formatter = logging.Formatter(config.format, config.datefmt)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger


def setup_logging(config: LoggingConfig, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Setup root logger with configuration.
    
    Args:
        config: Logging configuration
        log_file: Optional log file path
        
    Returns:
        Root logger instance
    """
    return LoggerFactory.create_logger('root', config, log_file)
