import logging
import sys
from typing import Any, Dict
import structlog
from src.core.config import settings


def setup_logging():
    """Setup structured logging configuration"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper())
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class AuditLogger:
    """Audit logger for tracking configuration changes"""
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    def log_config_created(self, user: str, config_id: int, config_name: str):
        """Log configuration creation"""
        self.logger.info(
            "Config created",
            action="create",
            user=user,
            config_id=config_id,
            config_name=config_name
        )
    
    def log_config_updated(self, user: str, config_id: int, config_name: str, changes: Dict[str, Any]):
        """Log configuration update"""
        self.logger.info(
            "Config updated",
            action="update",
            user=user,
            config_id=config_id,
            config_name=config_name,
            changes=changes
        )
    
    def log_config_deleted(self, user: str, config_id: int, config_name: str):
        """Log configuration deletion"""
        self.logger.info(
            "Config deleted",
            action="delete",
            user=user,
            config_id=config_id,
            config_name=config_name
        )
    
    def log_job_triggered(self, user: str, config_id: int, task_id: str):
        """Log manual job trigger"""
        self.logger.info(
            "Job manually triggered",
            action="trigger_job",
            user=user,
            config_id=config_id,
            task_id=task_id
        )


# Global audit logger instance
audit_logger = AuditLogger()