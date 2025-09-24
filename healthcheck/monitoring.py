#!/usr/bin/env python3
"""
Health Check Monitoring and Alerting System

This module provides continuous monitoring, scheduling, logging, and alerting
capabilities for the health check system.
"""

import asyncio
import json
import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import threading
import schedule

# Import health check modules
from .api_validators import run_all_api_validations
from .dependency_checker import run_all_dependency_checks
from .e2e_tests import run_all_e2e_tests
from .config_validator import run_all_config_validations

logger = logging.getLogger(__name__)


class HealthCheckScheduler:
    """Scheduler for running health checks at regular intervals."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.running = False
        self.scheduler_thread = None
        self.last_results = {}
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        self.history_manager = HealthCheckHistory(self.config.get('history', {}))
        
        # Default intervals (in minutes)
        self.intervals = {
            'api_checks': self.config.get('api_check_interval', 15),
            'dependency_checks': self.config.get('dependency_check_interval', 5),
            'e2e_tests': self.config.get('e2e_test_interval', 30),
            'config_checks': self.config.get('config_check_interval', 60)
        }
    
    def start(self):
        """Start the health check scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        
        # Schedule health checks
        schedule.every(self.intervals['api_checks']).minutes.do(self._run_api_checks)
        schedule.every(self.intervals['dependency_checks']).minutes.do(self._run_dependency_checks)
        schedule.every(self.intervals['e2e_tests']).minutes.do(self._run_e2e_tests)
        schedule.every(self.intervals['config_checks']).minutes.do(self._run_config_checks)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Health check scheduler started")
        
        # Run initial checks
        self._run_all_checks()
    
    def stop(self):
        """Stop the health check scheduler."""
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Health check scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(5)
    
    def _run_api_checks(self):
        """Run API validation checks."""
        try:
            logger.info("Running API validation checks")
            results = run_all_api_validations()
            self._process_results('api_checks', results)
        except Exception as e:
            logger.error(f"API checks failed: {e}")
    
    def _run_dependency_checks(self):
        """Run dependency checks."""
        try:
            logger.info("Running dependency checks")
            results = asyncio.run(run_all_dependency_checks())
            self._process_results('dependency_checks', results)
        except Exception as e:
            logger.error(f"Dependency checks failed: {e}")
    
    def _run_e2e_tests(self):
        """Run end-to-end tests."""
        try:
            logger.info("Running E2E tests")
            results = asyncio.run(run_all_e2e_tests())
            self._process_results('e2e_tests', results)
        except Exception as e:
            logger.error(f"E2E tests failed: {e}")
    
    def _run_config_checks(self):
        """Run configuration validation checks."""
        try:
            logger.info("Running configuration checks")
            results = run_all_config_validations()
            self._process_results('config_checks', results)
        except Exception as e:
            logger.error(f"Configuration checks failed: {e}")
    
    def _run_all_checks(self):
        """Run all health checks immediately."""
        self._run_api_checks()
        self._run_dependency_checks()
        self._run_e2e_tests()
        self._run_config_checks()
    
    def _process_results(self, check_type: str, results: List[Tuple[str, str, str, Dict[str, Any]]]):
        """Process health check results."""
        timestamp = datetime.utcnow().isoformat()
        
        # Store results
        self.last_results[check_type] = {
            'timestamp': timestamp,
            'results': results
        }
        
        # Save to history
        self.history_manager.save_results(check_type, results, timestamp)
        
        # Check for alerts
        self.alert_manager.check_and_send_alerts(check_type, results, timestamp)
        
        # Log summary
        passed = sum(1 for _, status, _, _ in results if status == "pass")
        failed = sum(1 for _, status, _, _ in results if status == "fail")
        warnings = sum(1 for _, status, _, _ in results if status == "warning")
        
        logger.info(f"{check_type}: {passed} passed, {failed} failed, {warnings} warnings")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        return {
            'running': self.running,
            'intervals': self.intervals,
            'last_results': {
                check_type: {
                    'timestamp': data['timestamp'],
                    'summary': {
                        'total': len(data['results']),
                        'passed': sum(1 for _, status, _, _ in data['results'] if status == "pass"),
                        'failed': sum(1 for _, status, _, _ in data['results'] if status == "fail"),
                        'warnings': sum(1 for _, status, _, _ in data['results'] if status == "warning")
                    }
                }
                for check_type, data in self.last_results.items()
            }
        }


class AlertManager:
    """Manages alerts and notifications for health check failures."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.alert_history = {}
        self.cooldown_period = timedelta(minutes=self.config.get('cooldown_minutes', 30))
        
        # Alert thresholds
        self.thresholds = {
            'critical_failure_count': self.config.get('critical_failure_count', 2),
            'warning_threshold': self.config.get('warning_threshold', 3),
            'consecutive_failures': self.config.get('consecutive_failures', 3)
        }
        
        # Notification settings
        self.notifications = {
            'email_enabled': self.config.get('email_enabled', False),
            'webhook_enabled': self.config.get('webhook_enabled', False),
            'log_enabled': self.config.get('log_enabled', True)
        }
    
    def check_and_send_alerts(self, check_type: str, results: List[Tuple[str, str, str, Dict[str, Any]]], timestamp: str):
        """Check results and send alerts if necessary."""
        failed_checks = [r for r in results if r[1] == "fail"]
        warning_checks = [r for r in results if r[1] == "warning"]
        
        # Check for critical failures
        if len(failed_checks) >= self.thresholds['critical_failure_count']:
            self._send_alert(
                'critical',
                f"Critical failures in {check_type}",
                f"{len(failed_checks)} checks failed: {[r[0] for r in failed_checks]}",
                check_type,
                timestamp
            )
        
        # Check for warning threshold
        elif len(warning_checks) >= self.thresholds['warning_threshold']:
            self._send_alert(
                'warning',
                f"Multiple warnings in {check_type}",
                f"{len(warning_checks)} checks have warnings: {[r[0] for r in warning_checks]}",
                check_type,
                timestamp
            )
        
        # Track consecutive failures
        self._track_consecutive_failures(check_type, failed_checks, timestamp)
    
    def _track_consecutive_failures(self, check_type: str, failed_checks: List, timestamp: str):
        """Track consecutive failures for escalation."""
        if check_type not in self.alert_history:
            self.alert_history[check_type] = {'consecutive_failures': 0, 'last_failure': None}
        
        if failed_checks:
            self.alert_history[check_type]['consecutive_failures'] += 1
            self.alert_history[check_type]['last_failure'] = timestamp
            
            if self.alert_history[check_type]['consecutive_failures'] >= self.thresholds['consecutive_failures']:
                self._send_alert(
                    'escalated',
                    f"Consecutive failures in {check_type}",
                    f"{self.alert_history[check_type]['consecutive_failures']} consecutive failures",
                    check_type,
                    timestamp
                )
        else:
            # Reset consecutive failures on success
            self.alert_history[check_type]['consecutive_failures'] = 0
    
    def _send_alert(self, severity: str, title: str, message: str, check_type: str, timestamp: str):
        """Send alert through configured channels."""
        alert_key = f"{check_type}_{severity}"
        
        # Check cooldown
        if self._is_in_cooldown(alert_key, timestamp):
            return
        
        alert_data = {
            'severity': severity,
            'title': title,
            'message': message,
            'check_type': check_type,
            'timestamp': timestamp
        }
        
        # Send through enabled channels
        if self.notifications['log_enabled']:
            self._send_log_alert(alert_data)
        
        if self.notifications['email_enabled']:
            self._send_email_alert(alert_data)
        
        if self.notifications['webhook_enabled']:
            self._send_webhook_alert(alert_data)
        
        # Record alert
        self.alert_history[alert_key] = {'last_sent': timestamp}
    
    def _is_in_cooldown(self, alert_key: str, current_timestamp: str) -> bool:
        """Check if alert is in cooldown period."""
        if alert_key not in self.alert_history:
            return False
        
        last_sent = self.alert_history[alert_key].get('last_sent')
        if not last_sent:
            return False
        
        last_sent_dt = datetime.fromisoformat(last_sent)
        current_dt = datetime.fromisoformat(current_timestamp)
        
        return current_dt - last_sent_dt < self.cooldown_period
    
    def _send_log_alert(self, alert_data: Dict[str, Any]):
        """Send alert to logs."""
        severity_levels = {
            'critical': logging.CRITICAL,
            'escalated': logging.ERROR,
            'warning': logging.WARNING
        }
        
        level = severity_levels.get(alert_data['severity'], logging.WARNING)
        logger.log(level, f"HEALTH ALERT: {alert_data['title']} - {alert_data['message']}")
    
    def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send email alert."""
        try:
            # Email configuration from environment or config
            smtp_server = self.config.get('smtp_server', os.getenv('SMTP_SERVER'))
            smtp_port = self.config.get('smtp_port', int(os.getenv('SMTP_PORT', 587)))
            smtp_username = self.config.get('smtp_username', os.getenv('SMTP_USERNAME'))
            smtp_password = self.config.get('smtp_password', os.getenv('SMTP_PASSWORD'))
            from_email = self.config.get('from_email', os.getenv('ALERT_FROM_EMAIL'))
            to_emails = self.config.get('to_emails', os.getenv('ALERT_TO_EMAILS', '').split(','))
            
            if not all([smtp_server, smtp_username, smtp_password, from_email, to_emails]):
                logger.warning("Email alert configuration incomplete")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[{alert_data['severity'].upper()}] {alert_data['title']}"
            
            body = f"""
Health Check Alert

Severity: {alert_data['severity'].upper()}
Check Type: {alert_data['check_type']}
Time: {alert_data['timestamp']}

Message: {alert_data['message']}

This is an automated alert from the JJF Survey Analytics health monitoring system.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent: {alert_data['title']}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_webhook_alert(self, alert_data: Dict[str, Any]):
        """Send webhook alert."""
        try:
            import requests
            
            webhook_url = self.config.get('webhook_url', os.getenv('ALERT_WEBHOOK_URL'))
            if not webhook_url:
                logger.warning("Webhook URL not configured")
                return
            
            payload = {
                'text': f"🚨 Health Alert: {alert_data['title']}",
                'attachments': [{
                    'color': 'danger' if alert_data['severity'] == 'critical' else 'warning',
                    'fields': [
                        {'title': 'Severity', 'value': alert_data['severity'], 'short': True},
                        {'title': 'Check Type', 'value': alert_data['check_type'], 'short': True},
                        {'title': 'Message', 'value': alert_data['message'], 'short': False},
                        {'title': 'Time', 'value': alert_data['timestamp'], 'short': True}
                    ]
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent: {alert_data['title']}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")


class HealthCheckHistory:
    """Manages historical health check data."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.history_dir = Path(self.config.get('history_dir', 'healthcheck_history'))
        self.history_dir.mkdir(exist_ok=True)
        
        self.retention_days = self.config.get('retention_days', 30)
        self.max_file_size = self.config.get('max_file_size_mb', 10) * 1024 * 1024
    
    def save_results(self, check_type: str, results: List[Tuple[str, str, str, Dict[str, Any]]], timestamp: str):
        """Save health check results to history."""
        try:
            date_str = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d')
            history_file = self.history_dir / f"{check_type}_{date_str}.jsonl"
            
            # Prepare data
            record = {
                'timestamp': timestamp,
                'check_type': check_type,
                'results': [
                    {
                        'name': name,
                        'status': status,
                        'message': message,
                        'details': details
                    }
                    for name, status, message, details in results
                ]
            }
            
            # Append to file
            with open(history_file, 'a') as f:
                f.write(json.dumps(record) + '\n')
            
            # Check file size and rotate if necessary
            if history_file.stat().st_size > self.max_file_size:
                self._rotate_file(history_file)
            
            # Clean old files
            self._cleanup_old_files()
            
        except Exception as e:
            logger.error(f"Failed to save health check history: {e}")
    
    def _rotate_file(self, file_path: Path):
        """Rotate log file when it gets too large."""
        try:
            timestamp = datetime.now().strftime('%H%M%S')
            rotated_path = file_path.with_suffix(f'.{timestamp}.jsonl')
            file_path.rename(rotated_path)
            logger.info(f"Rotated history file: {rotated_path}")
        except Exception as e:
            logger.error(f"Failed to rotate history file: {e}")
    
    def _cleanup_old_files(self):
        """Remove old history files beyond retention period."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for file_path in self.history_dir.glob('*.jsonl'):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    logger.info(f"Removed old history file: {file_path}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old history files: {e}")
    
    def get_history(self, check_type: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get historical data for a check type."""
        history = []
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for file_path in self.history_dir.glob(f"{check_type}_*.jsonl"):
                if file_path.stat().st_mtime >= cutoff_date.timestamp():
                    with open(file_path, 'r') as f:
                        for line in f:
                            try:
                                record = json.loads(line.strip())
                                history.append(record)
                            except json.JSONDecodeError:
                                continue
            
            # Sort by timestamp
            history.sort(key=lambda x: x['timestamp'])
            
        except Exception as e:
            logger.error(f"Failed to get history for {check_type}: {e}")
        
        return history


def create_monitoring_config() -> Dict[str, Any]:
    """Create default monitoring configuration."""
    return {
        'api_check_interval': 15,  # minutes
        'dependency_check_interval': 5,
        'e2e_test_interval': 30,
        'config_check_interval': 60,
        'alerts': {
            'cooldown_minutes': 30,
            'critical_failure_count': 2,
            'warning_threshold': 3,
            'consecutive_failures': 3,
            'email_enabled': False,
            'webhook_enabled': False,
            'log_enabled': True
        },
        'history': {
            'history_dir': 'healthcheck_history',
            'retention_days': 30,
            'max_file_size_mb': 10
        }
    }


if __name__ == "__main__":
    """Run monitoring system as standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Health Check Monitoring System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    # Load configuration
    config = create_monitoring_config()
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config.update(json.load(f))
    
    # Create and start scheduler
    scheduler = HealthCheckScheduler(config)
    
    try:
        scheduler.start()
        
        if args.daemon:
            # Run as daemon
            while True:
                time.sleep(60)
                status = scheduler.get_status()
                logger.info(f"Monitoring status: {status}")
        else:
            # Run for a short time and exit
            time.sleep(10)
            status = scheduler.get_status()
            print(json.dumps(status, indent=2))
            
    except KeyboardInterrupt:
        logger.info("Shutting down monitoring system")
    finally:
        scheduler.stop()
