import logging

from sarvamai import SarvamAI

from app.core.config import settings

logger = logging.getLogger("datly.ai.sarvam")

class SarvamClient:
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.client: SarvamAI | None = None
        
        if not self.api_key:
            logger.warning("SARVAM_API_KEY is missing! Voice features will be unavailable.")
        else:
            try:
                self.client = SarvamAI(api_subscription_key=self.api_key)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to initialize Sarvam SDK: {e!s}")

    def get_client(self) -> SarvamAI | None:
        if not self.client and settings.SARVAM_API_KEY:
            self.api_key = settings.SARVAM_API_KEY
            try:
                self.client = SarvamAI(api_subscription_key=self.api_key)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to initialize Sarvam SDK: {e!s}")
        return self.client

sarvam_client = SarvamClient()
