import os
from dotenv import load_dotenv
from gemini_provider import GeminiProvider
from ollama_provider import OllamaProvider

load_dotenv()

# Local Model Registry mapping user-friendly names to specific provider and model settings
MODEL_REGISTRY = {
    "Gemini": {
        "provider_class": GeminiProvider,
        "default_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "default_settings": {}
    },
    "Rogue Creative": {
        "provider_class": OllamaProvider,
        "default_model": "hf.co/DavidAU/L3.2-Rogue-Creative-Instruct-Uncensored-Abliterated-7B-GGUF:Q4_K_M",
        "default_settings": {
            "temperature": 0.95,
            "top_p": 0.92,
            "repeat_penalty": 1.08,
            "num_ctx": 4096,
            "num_predict": 1400
        }
    }
}

def get_ai_provider(provider_type: str = None, generation_settings: dict = None):
    """
    Factory function to return the configured AI provider.
    Supports: 'Gemini', 'Rogue Creative', as well as legacy 'gemini', 'ollama' / 'qwen' strings.
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
        
        if registry_match == "Rogue Creative":
            kwargs = {
                "model_name": cfg["default_model"]
            }
            # Merge model registry defaults with any dynamic UI generation overrides
            settings = dict(cfg["default_settings"])
            if generation_settings:
                settings.update(generation_settings)
            kwargs.update(settings)
            return provider_class(**kwargs)
        else:
            # For Gemini, instantiate normally
            return provider_class()

    # 2. Fallback to legacy behavior for backward compatibility (e.g., matching 'gemini' or 'qwen')
    provider_type_lower = provider_type.lower()
    if provider_type_lower in ("gemini", "google"):
        return GeminiProvider()
    elif provider_type_lower in ("ollama", "qwen", "qwen local", "qwen_local"):
        kwargs = {}
        if generation_settings:
            kwargs.update(generation_settings)
        return OllamaProvider(**kwargs)
    else:
        raise ValueError(f"Unsupported AI provider or engine: {provider_type}")

