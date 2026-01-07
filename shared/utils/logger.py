"""
Structured logging setup for microservices
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional
import uuid

from shared.config import LOG_LEVEL, LOG_FORMAT


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'service': getattr(record, 'service', 'unknown'),
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add correlation ID if present
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logger(
    service_name: str,
    log_level: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Setup structured logger for a microservice
    
    Args:
        service_name: Name of the service (e.g., 'sheets-service')
        log_level: Log level (defaults to LOG_LEVEL from config)
        log_format: Log format ('json' or 'text', defaults to LOG_FORMAT from config)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(log_level or LOG_LEVEL)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    if (log_format or LOG_FORMAT) == 'json':
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Add service name to all log records
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    return logger


def get_logger(service_name: str) -> logging.Logger:
    """Get logger for a service (creates if doesn't exist)"""
    logger = logging.getLogger(service_name)
    if not logger.handlers:
        return setup_logger(service_name)
    return logger


def generate_correlation_id() -> str:
    """Generate a correlation ID for request tracing"""
    return str(uuid.uuid4())

