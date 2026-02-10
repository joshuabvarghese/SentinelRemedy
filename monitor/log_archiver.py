import boto3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("DBMonitor.Archiver")

class LogArchiver:
    def __init__(self, bucket, region="us-east-1"):
        self.bucket = bucket
        self.region = region

    def backup(self, log_path):
        if not self.bucket:
            return
        try:
            s3 = boto3.client('s3', region_name=self.region)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path(log_path)
            
            for log_file in log_dir.glob("*.log"):
                s3_key = f"db_logs/{timestamp}/{log_file.name}"
                s3.upload_file(str(log_file), self.bucket, s3_key)
                logger.info(f"Archived {log_file.name} to S3")
        except Exception as e:
            logger.error(f"S3 Backup failed: {e}")