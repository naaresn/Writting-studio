import os
import logging
from google import genai
from ai_provider import AIProvider

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiProvider(AIProvider):
    """Implementation of AIProvider for Google's Gemini API."""

    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        try:
            logger.info(f"Sending prompt to Gemini ({self.model_name})...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            if response and response.text:
                logger.info("Successfully received Gemini response.")
                return response.text

            # If we reach here, response is empty or response.text is empty/None
            logger.error(f"Gemini returned an empty response. Raw response: {response}")
            raise ValueError("AI returned an empty response.")

        except Exception as e:
            logger.exception(f"Gemini API Error: {str(e)}")
            raise e

