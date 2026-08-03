from bible_manager import load_bible
from database import get_latest_story_context, save_chapter
from provider_factory import get_ai_provider
from prompt_builder import PromptBuilder
from summary_builder import SummaryBuilder
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class StoryService:
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.summary_builder = SummaryBuilder()

    def generate_chapter(
        self, 
        project_id: int, 
        project_name: str, 
        title: str, 
        storyline: str, 
        tone: str, 
        length: str,
        provider_name: str = "gemini",
        writing_profile: str = "standard"
    ) -> Dict[str, Any]:
        """
        Coordinates the chapter generation workflow.
        """
        # 1. Load the project's Story Bible
        bible = load_bible(project_name)

        # 2. Get the requested provider
        ai_provider = get_ai_provider(provider_name)
        model_name = getattr(ai_provider, 'model_name', provider_name)

        # 3. Retrieve previous story context
        context = get_latest_story_context(project_id, limit=5)
        
        # 4. Build the chapter prompt
        prompt = self.prompt_builder.build_chapter_prompt(
            bible=bible,
            storyline=storyline,
            tone=tone,
            length=length,
            writing_profile=writing_profile,
            previous_summaries=context
        )

        # 5. Generate the chapter
        try:
            content = ai_provider.generate(prompt)
        except Exception as e:
            logger.error(f"Failed to generate chapter: {e}")
            raise Exception(f"Chapter generation failed: {str(e)}")

        # 6. Build a summary prompt
        summary_prompt = self.summary_builder.build_summary_prompt(content)

        # 7. Generate the chapter summary
        try:
            summary = ai_provider.generate(summary_prompt)
        except Exception as e:
            logger.error(f"Failed to generate chapter summary: {e}")
            raise Exception(f"Summary generation failed: {str(e)}")

        # 8. Save the chapter
        chapter_id = save_chapter(
            project_id=project_id,
            title=title,
            storyline=storyline,
            content=content,
            tone=tone,
            length=length,
            summary=summary,
            provider=provider_name,
            model=model_name,
            writing_profile=writing_profile
        )

        # 9. Return result
        return {
            "chapter_id": chapter_id,
            "content": content,
            "summary": summary
        }
