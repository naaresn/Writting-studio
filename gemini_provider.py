import os
import logging
from google import genai
from ai_provider import AIProvider
import time

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
        # Daftar model cadangan jika model utama sibuk (503)
        fallback_models = [
            self.model_name,
            "models/gemini-2.5-flash",
            "models/gemini-1.5-flash"
        ]
        # Hilangkan duplikat sambil mempertahankan urutan
        models_to_try = list(dict.fromkeys(fallback_models))

        for current_model in models_to_try:
            # Coba maksimal 3 kali per model jika kena 503
            for attempt in range(3):
                try:
                    logger.info(f"Sending prompt to Gemini ({current_model}) [Attempt {attempt + 1}]...")
                    response = self.client.models.generate_content(
                        model=current_model,
                        contents=prompt
                    )

                    if response and response.text:
                        logger.info("Successfully received Gemini response.")
                        return response.text

                    logger.error(f"Gemini returned an empty response. Raw response: {response}")
                    raise ValueError("AI returned an empty response.")

                except Exception as e:
                    error_msg = str(e)
                    # Jika kena error 503 / UNAVAILABLE, tunggu lalu retry atau pindah model
                    if "503" in error_msg or "UNAVAILABLE" in error_msg:
                        wait_time = 2 ** (attempt + 1)
                        logger.warning(f"503 Server Busy on {current_model}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    
                    # Jika error lain (bukan 503), langsung raise error
                    logger.exception(f"Gemini API Error: {error_msg}")
                    raise e

        raise RuntimeError("Semua model Gemini sedang sibuk (503 UNAVAILABLE). Silakan coba beberapa saat lagi.")


    # def generate(self, prompt: str) -> str:
    #     try:
    #         logger.info(f"Sending prompt to Gemini ({self.model_name})...")
    #         response = self.client.models.generate_content(
    #             model=self.model_name,
    #             contents=prompt
    #         )

    #         if response and response.text:
    #             logger.info("Successfully received Gemini response.")
    #             return response.text

    #         # If we reach here, response is empty or response.text is empty/None
    #         logger.error(f"Gemini returned an empty response. Raw response: {response}")
    #         raise ValueError("AI returned an empty response.")

    #     except Exception as e:
    #         logger.exception(f"Gemini API Error: {str(e)}")
    #         raise e

