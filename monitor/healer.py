import subprocess
import logging
import time

logger = logging.getLogger("DBMonitor.Healer")

class Healer:
    def __init__(self, restart_command):
        self.command = restart_command

    def recover(self):
        try:
            logger.info(f"Executing: {self.command}")
            subprocess.run(self.command, shell=True, check=True)
            time.sleep(15) # Warm-up period
            return True
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            return False