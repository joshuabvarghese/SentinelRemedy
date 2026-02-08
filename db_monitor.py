#!/usr/bin/env python3
"""
Self-Healing Database Monitor
Monitors PostgreSQL database health and automatically recovers from failures.
"""

import os
import time
import logging
import subprocess
import psycopg2
import boto3
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configuration from environment variables
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Monitoring configuration
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '30'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RESTART_COMMAND = os.getenv('RESTART_COMMAND', 'docker-compose restart postgres')

# Notification configuration
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')

# AWS S3 configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', '')
LOG_BACKUP_PATH = os.getenv('LOG_BACKUP_PATH', '/var/lib/postgresql/data/pg_log')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("db_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DBMonitor")

class DatabaseMonitor:
    def __init__(self):
        self.consecutive_failures = 0
        self.last_healthy_time = datetime.now()
        
    def check_database_health(self) -> bool:
        """Attempts to connect to the database to verify health."""
        conn = None
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=5
            )
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def backup_logs_to_s3(self):
        """Backs up database logs to S3 before a restart for post-mortem analysis."""
        if not S3_BUCKET:
            logger.info("S3_BUCKET not configured, skipping log backup")
            return

        try:
            s3 = boto3.client('s3', region_name=AWS_REGION)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            log_dir = Path(LOG_BACKUP_PATH)
            if not log_dir.exists():
                logger.warning(f"Log directory {LOG_BACKUP_PATH} not found")
                return

            for log_file in log_dir.glob("*.log"):
                s3_key = f"db_logs/{timestamp}/{log_file.name}"
                s3.upload_file(str(log_file), S3_BUCKET, s3_key)
                logger.info(f"Uploaded {log_file.name} to S3 bucket {S3_BUCKET}")
                
        except Exception as e:
            logger.error(f"Failed to backup logs to S3: {e}")

    def send_notification(self, message: str, is_recovery: bool = False):
        """Sends alerts to Discord or Slack."""
        payload = {
            "content": f"{'✅ RECOVERY' if is_recovery else '🚨 ALERT'}: {message}"
        }
        
        for url in [DISCORD_WEBHOOK_URL, SLACK_WEBHOOK_URL]:
            if url:
                try:
                    requests.post(url, json=payload, timeout=5)
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")

    def handle_database_failure(self):
        """Increments failure count and triggers recovery if threshold is met."""
        self.consecutive_failures += 1
        logger.warning(f"Failure count: {self.consecutive_failures}/{MAX_RETRIES}")
        
        if self.consecutive_failures == 1:
            self.send_notification(f"Database connection issues detected on {DB_HOST}")
            
        if self.consecutive_failures >= MAX_RETRIES:
            logger.error("Max retries reached. Initiating auto-healing recovery...")
            self.backup_logs_to_s3()
            self.perform_recovery()

    def perform_recovery(self):
        """Executes the restart command to heal the database."""
        try:
            logger.info(f"Executing recovery command: {RESTART_COMMAND}")
            result = subprocess.run(RESTART_COMMAND, shell=True, check=True, capture_output=True)
            logger.info("Recovery command executed successfully")
            self.send_notification("Recovery command executed. Waiting for database to stabilize...")
            time.sleep(15) # Wait for DB to boot
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            self.send_notification(f"CRITICAL: Recovery command failed: {e}")

    def handle_database_recovery(self):
        """Reset state when database becomes healthy again."""
        if self.consecutive_failures > 0:
            recovery_message = (
                f"Database recovered and is now healthy!\n"
                f"Previous failures: {self.consecutive_failures}"
            )
            self.send_notification(recovery_message, is_recovery=True)
        
        self.consecutive_failures = 0
        self.last_healthy_time = datetime.now()
    
    def run(self):
        """Main monitoring loop."""
        logger.info("Database monitor started")
        while True:
            try:
                is_healthy = self.check_database_health()
                if is_healthy:
                    self.handle_database_recovery()
                else:
                    self.handle_database_failure()
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor = DatabaseMonitor()
    monitor.run()
