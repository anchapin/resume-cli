import logging
import os

from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key(api_key: str = Security(api_key_header)):
    expected_api_key = os.getenv("RESUME_API_KEY")

    if not expected_api_key:
        # Secure by default: Require explicit opt-in for insecure mode
        insecure_mode = os.getenv("RESUME_INSECURE_MODE", "").lower() == "true"

        if insecure_mode:
            logger.warning("Running in INSECURE MODE. Authentication is disabled.")
            return api_key

        logger.error("Authentication failed: RESUME_API_KEY not set and secure mode is active.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: RESUME_API_KEY not set. Set RESUME_API_KEY or RESUME_INSECURE_MODE=true.",
        )

    if api_key == expected_api_key:
        return api_key

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )
