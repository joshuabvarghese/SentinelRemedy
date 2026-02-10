import os
import time
import psycopg2
import logging
from notifier import Notifier
from log_archiver import LogArchiver
from healer import Healer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DBMonitor")

class DatabaseMonitor:
    def __init__(self):
        self.failures = 0
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.notifier = Notifier(os.getenv('DISCORD_WEBHOOK_URL'), os.getenv('SLACK_WEBHOOK_URL'))
        self.archiver = LogArchiver(os.getenv('S3_BUCKET'), os.getenv('AWS_REGION'))
        self.healer = Healer(os.getenv('RESTART_COMMAND', 'docker-compose restart postgres'))

    def check(self):
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                connect_timeout=5
            )
            conn.close()
            return True
        except:
            return False

    def run(self):
        logger.info("SentinelRemedy active...")
        while True:
            if self.check():
                if self.failures > 0:
                    self.notifier.send("Database restored.", is_recovery=True)
                self.failures = 0
            else:
                self.failures += 1
                logger.warning(f"Health check failed ({self.failures}/{self.max_retries})")
                if self.failures == self.max_retries:
                    self.archiver.backup('/var/lib/postgresql/data/pg_log')
                    self.healer.recover()
                    self.notifier.send("Critical failure detected. Recovery initiated.")
            time.sleep(int(os.getenv('CHECK_INTERVAL', '30')))

if __name__ == "__main__":
    monitor = DatabaseMonitor()
    monitor.run()