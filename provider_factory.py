import os
from gemini_provider import GeminiProvider
from ollama_provider import OllamaProvider
import logging

logger = logging.getLogger(__name__)

# Local Model Registry mapping user-friendly names to specific provider and model settings
MODEL_REGISTRY = {
    "Gemini": {
        "provider_class": GeminiProvider,
        "default_model_env": "GEMINI_MODEL",
        "default_model": "gemini-1.5-flash",
        "default_settings": {}
    },
    "Qwen Local": {
        "provider_class": OllamaProvider,
        "default_model_env": "OLLAMA_QWEN_MODEL",
        "default_model": "qwen2.5:3b",
        "default_settings": {
            "temperature": 0.85,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "num_ctx": 4096,
            "num_predict": 1400
        }
    },
    "Gemma Creative": {
        "provider_class": OllamaProvider,
        "default_model_env": "OLLAMA_GEMMA_MODEL",
        "default_model": "hf.co/DavidAU/Gemma-3-it-4B-Uncensored-DBL-X-GGUF:Q4_K_M",
        "default_settings": {
            "temperature": 0.95,
            "top_p": 0.92,
            "repeat_penalty": 1.08,
            "num_ctx": 4096,
            "num_predict": 1400
        }
    }
}

def get_model_name(provider_key):
    cfg = MODEL_REGISTRY.get(provider_key)
    if not cfg:
        return None
    model = os.getenv(cfg["default_model_env"], cfg["default_model"])
    logger.info(f"Using model for {provider_key}: {model}")
    return model

def get_ai_provider(provider_type: str = None, generation_settings: dict = None):
    """
    Factory function to return the configured AI provider.
    """
    if provider_type is None:
        provider_type = os.getenv("AI_PROVIDER", "Gemini")

    # 1. Search in MODEL_REGISTRY first (case-insensitive lookup)
    registry_match = None
    for key in MODEL_REGISTRY:
        if key.lower() == provider_type.lower():
            registry_match = key
            break

    if registry_match:
        cfg = MODEL_REGISTRY[registry_match]
        provider_class = cfg["provider_class"]

        model_name = get_model_name(registry_match)

        # Merge model registry defaults with any dynamic UI generation overrides
        settings = dict(cfg["default_settings"])
        if generation_settings:
            settings.update(generation_settings)
            
        if registry_match == "Gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            return provider_class(api_key=api_key, model_name=model_name)
        else:
            kwargs = {"model_name": model_name}
            kwargs.update(settings)
            return provider_class(**kwargs)

    # 2. Fallback to legacy behavior
    raise ValueError(f"Unknown AI provider: {provider_type}")
