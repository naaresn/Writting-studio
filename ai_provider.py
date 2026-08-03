from abc import ABC, abstractmethod

class AIProvider(ABC):
    """Abstract base class for AI model providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Sends a prompt to the AI model and returns the generated text.
        
        Args:
            prompt (str): The full structured prompt.
            
        Returns:
            str: The generated content.
        """
        pass
