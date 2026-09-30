import os
import re
import logging
from openai import OpenAI
from ai_provider import AIProvider

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenRouterProvider(AIProvider):
    """Implementation of AIProvider for OpenRouter API running Qwen or other hosted models."""

    def __init__(
        self,
        api_key: str = None,
        model_name: str = None,
        temperature: float = None,
        top_p: float = None,
        max_tokens: int = None
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model_name or os.getenv("OPENROUTER_MODEL", "qwen/qwen3.8-27b:free")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

        # Generation parameters with sensible defaults
        try:
            self.temperature = temperature if temperature is not None else float(os.getenv("OPENROUTER_TEMPERATURE", "0.85"))
        except ValueError:
            self.temperature = 0.85

        try:
            self.top_p = top_p if top_p is not None else float(os.getenv("OPENROUTER_TOP_P", "0.9"))
        except ValueError:
            self.top_p = 0.9

        try:
            self.max_tokens = max_tokens if max_tokens is not None else int(os.getenv("OPENROUTER_MAX_TOKENS", "4096"))
        except ValueError:
            self.max_tokens = 4096

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/naaresn/writter-studio",
                "X-Title": "Story Studio"
            }
        )

    def generate(self, prompt: str) -> str:
        """
        Sends a prompt to OpenRouter API and returns the generated text.
        """
        try:
            logger.info(f"Sending prompt to OpenRouter ({self.model_name})... Prompt length: {len(prompt)} chars.")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens
            )

            if response and response.choices and len(response.choices) > 0:
                text = response.choices[0].message.content or ""
                if not text.strip():
                    logger.error(f"OpenRouter returned empty content. Full response: {response}")
                    raise ValueError("AI returned an empty response.")

                # Strip out reasoning/planning text like <think>...</think> if model outputs them
                text = self._strip_reasoning_text(text)
                logger.info("Successfully received OpenRouter response.")
                return text

            logger.error(f"OpenRouter returned an unexpected response structure: {response}")
            raise ValueError("AI returned an empty response.")

        except Exception as e:
            logger.exception(f"OpenRouter API Error: {str(e)}")
            raise e

    def _strip_reasoning_text(self, text: str) -> str:
        """
        Removes any thinking/reasoning blocks, such as <think>...</think>
        to ensure no planning/reasoning metadata is exposed in the final output.
        """
        text = re.sub(r'(?i)<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'(?i)<think>', '', text)
        text = re.sub(r'(?i)</think>', '', text)
        return text.strip()
