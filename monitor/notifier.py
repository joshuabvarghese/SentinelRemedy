import requests
import logging

logger = logging.getLogger("DBMonitor.Notifier")

class Notifier:
    def __init__(self, discord_url=None, slack_url=None):
        self.urls = [url for url in [discord_url, slack_url] if url]

    def send(self, message, is_recovery=False):
        payload = {"content": f"{'✅ RECOVERY' if is_recovery else '🚨 ALERT'}: {message}"}
        for url in self.urls:
            try:
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")