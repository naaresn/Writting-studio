from prompt_builder import PromptBuilder
from ollama_provider import OllamaProvider
import system_prompts

print("Modules imported successfully.")
print("OLLAMA prompt defined:", hasattr(system_prompts, "OLLAMA_INDONESIAN_ROMANCE_PROMPT"))
pb = PromptBuilder()
print("PromptBuilder initialized.")
op = OllamaProvider(model_name="qwen2.5:3b")
print("OllamaProvider initialized.")
