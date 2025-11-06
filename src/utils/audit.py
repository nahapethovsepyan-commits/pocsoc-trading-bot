"""
Audit logging module for tracking sensitive operations.
"""

import os
import asyncio
import logging
import json
from datetime import datetime
from typing import Any, Optional
from pathlib import Path


AUDIT_LOG_DIR = "logs"
AUDIT_LOG_FILE = os.path.join(AUDIT_LOG_DIR, "audit.log")


def ensure_audit_log_dir():
    """Ensure audit log directory exists."""
    os.makedirs(AUDIT_LOG_DIR, exist_ok=True)


def _write_audit_log_sync(audit_entry: dict) -> None:
    """
    Synchronous helper function to write audit log entry.
    This is run in executor to avoid blocking the event loop.
    """
    try:
        with open(AUDIT_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')
    except Exception as e:
        logging.error(f"Failed to write audit log: {e}")


async def log_config_change(user_id: int, param: str, old_value: Any, new_value: Any) -> None:
    """
    Log configuration changes for audit trail.
    
    Args:
        user_id: Telegram user ID who made the change
        param: Configuration parameter name
        old_value: Previous value
        new_value: New value
    """
    ensure_audit_log_dir()
    
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'action': 'config_change',
        'parameter': param,
        'old_value': str(old_value),
        'new_value': str(new_value),
        'result': 'success'
    }
    
    try:
        # Use executor to avoid blocking event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _write_audit_log_sync, audit_entry)
        logging.debug(f"Audit log: Config change by user {user_id}: {param} = {old_value} -> {new_value}")
    except Exception as e:
        logging.error(f"Failed to write audit log: {e}")


async def log_admin_action(user_id: int, action: str, details: Optional[dict] = None) -> None:
    """
    Log admin actions for audit trail.
    
    Args:
        user_id: Telegram user ID who performed the action
        action: Action description
        details: Optional additional details dictionary
    """
    ensure_audit_log_dir()
    
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'action': action,
        'details': details or {},
        'result': 'success'
    }
    
    try:
        # Use executor to avoid blocking event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _write_audit_log_sync, audit_entry)
        logging.debug(f"Audit log: Admin action by user {user_id}: {action}")
    except Exception as e:
        logging.error(f"Failed to write audit log: {e}")


async def log_security_event(user_id: Optional[int], event_type: str, description: str, 
                            severity: str = 'medium') -> None:
    """
    Log security-related events for audit trail.
    
    Args:
        user_id: Telegram user ID (None if system event)
        event_type: Type of security event (e.g., 'rate_limit_exceeded', 'invalid_input')
        description: Event description
        severity: Event severity ('low', 'medium', 'high', 'critical')
    """
    ensure_audit_log_dir()
    
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'action': 'security_event',
        'event_type': event_type,
        'description': description,
        'severity': severity,
        'result': 'logged'
    }
    
    try:
        # Use executor to avoid blocking event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _write_audit_log_sync, audit_entry)
        
        # Log to main log with appropriate level based on severity
        if severity == 'critical':
            logging.critical(f"Security event: {event_type} - {description} (user: {user_id})")
        elif severity == 'high':
            logging.error(f"Security event: {event_type} - {description} (user: {user_id})")
        elif severity == 'medium':
            logging.warning(f"Security event: {event_type} - {description} (user: {user_id})")
        else:
            logging.info(f"Security event: {event_type} - {description} (user: {user_id})")
    except Exception as e:
        logging.error(f"Failed to write audit log: {e}")

