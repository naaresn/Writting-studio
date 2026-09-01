import os
import urllib.request
import urllib.error
import json
import re
import logging
from ai_provider import AIProvider

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaProvider(AIProvider):
    """Implementation of AIProvider for a local Ollama instance running Qwen or other creative fiction models."""

    def __init__(
        self,
        model_name: str,
        temperature: float = None,
        top_p: float = None,
        repeat_penalty: float = None,
        num_ctx: int = None,
        num_predict: int = None
    ):
        # Read environment variables with sensible defaults
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = model_name
        
        # Generation options with overrides from env vars or constructor arguments
        try:
            self.temperature = temperature if temperature is not None else float(os.getenv("OLLAMA_TEMPERATURE", "0.85"))
        except ValueError:
            self.temperature = 0.85
            
        try:
            self.top_p = top_p if top_p is not None else float(os.getenv("OLLAMA_TOP_P", "0.9"))
        except ValueError:
            self.top_p = 0.9
            
        try:
            self.repeat_penalty = repeat_penalty if repeat_penalty is not None else float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.1"))
        except ValueError:
            self.repeat_penalty = 1.1
            
        try:
            self.num_ctx = num_ctx if num_ctx is not None else int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        except ValueError:
            self.num_ctx = 4096
            
        try:
            self.num_predict = num_predict if num_predict is not None else int(os.getenv("OLLAMA_NUM_PREDICT", "1400"))
        except ValueError:
            self.num_predict = 1400

    def generate(self, prompt: str) -> str:
        url = f"{self.host.rstrip('/')}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repeat_penalty": self.repeat_penalty,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict
            }
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={"Content-Type": "application/json"}
        )
        
        # Log prompt length for debugging
        logger.info(f"Prompt length: {len(prompt)} characters.")
        
        try:
            logger.info(f"Sending prompt to Ollama ({self.model_name}) at {self.host}...")
            with urllib.request.urlopen(req, timeout=120) as response:
                res_data = response.read().decode("utf-8")
                res_json = json.loads(res_data)
                text = res_json.get("response", "")
                
                if not text:
                    logger.error(f"Ollama returned an empty response. Raw response: {res_json}")
                    raise ValueError("AI returned an empty response.")
                
                # Strip out reasoning/planning text like <think>...</think>
                text = self._strip_reasoning_text(text)
                logger.info("Successfully received Ollama response.")
                return text
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Exception(f"Model '{self.model_name}' not found on Ollama server at {self.host}. Please run 'ollama pull {self.model_name}'")
            else:
                logger.exception(f"Ollama HTTP Error: {e.code} - {e.reason}")
                raise Exception(f"Ollama API error ({e.code}): {e.reason}")
        except urllib.error.URLError as e:
            logger.exception(f"Ollama Connection Error: {str(e)}")
            raise ConnectionError(f"Could not connect to Ollama at {self.host}. Please ensure Ollama is running.")
        except Exception as e:
            logger.exception(f"Ollama Provider Error: {str(e)}")
            raise e

    def _strip_reasoning_text(self, text: str) -> str:
        """
        Removes any thinking/reasoning blocks, such as <think>...</think>
        to ensure no planning/reasoning metadata is exposed in the final output.
        """
        # Remove matching <think>...</think> blocks case-insensitively
        text = re.sub(r'(?i)<think>.*?</think>', '', text, flags=re.DOTALL)
        # Also clean up unclosed <think> or leftover tags if they happen to appear
        text = re.sub(r'(?i)<think>', '', text)
        text = re.sub(r'(?i)</think>', '', text)
        return text.strip()
