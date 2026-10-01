from bible_manager import load_bible
from relationship_manager import load_relationships
from database import get_latest_story_context, save_chapter, create_project, get_all_projects
from provider_factory import get_ai_provider
from prompt_builder import PromptBuilder
from summary_builder import SummaryBuilder
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class StoryService:
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.summary_builder = SummaryBuilder()

    def _get_or_create_oneshot_project(self) -> int:
        """
        Retrieves the ID of the 'One-Shots' project, creating it if it does not exist.
        """
        projects = get_all_projects()
        project = next((p for p in projects if p[1] == "One-Shots"), None)
        if project:
            return project[0]

        project_id = create_project("One-Shots")
        if project_id is not None:
            return project_id

        # In case create_project returned None due to existing name race condition
        projects = get_all_projects()
        project = next((p for p in projects if p[1] == "One-Shots"), None)
        if project:
            return project[0]

        raise Exception("Failed to create or retrieve 'One-Shots' project.")

    def generate_oneshot(
        self,
        storyline: str,
        tone: str,
        length: str,
        provider_name: str = "gemini",
        writing_profile: str = "standard",
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Coordinates generating a complete standalone story without project context.
        """
        # 1. Derive title if empty
        if not title or not str(title).strip():
            words = storyline.strip().split()
            clean_title = " ".join(words[:6]) if words else "Untitled One-Shot"
        else:
            clean_title = str(title).strip()

        # 2. Get the requested provider
        ai_provider = get_ai_provider(provider_name)
        model_name = getattr(ai_provider, 'model_name', provider_name)

        # 3. Build the one-shot prompt (omit bible, summaries, and relationship memory)
        provider_type = "ollama" if "ollama" in str(provider_name).lower() or "qwen local" in str(provider_name).lower() else "gemini"
        prompt = self.prompt_builder.build_chapter_prompt(
            bible={},
            storyline=storyline,
            tone=tone,
            length=length,
            writing_profile=writing_profile,
            previous_summaries=None,
            provider_type=provider_type,
            relationship_memory=None,
            mode="oneshot"
        )

        # 4. Generate the story content
        try:
            content = ai_provider.generate(prompt)
        except Exception as e:
            logger.error(f"Failed to generate story: {e}")
            raise Exception(f"Story generation failed: {str(e)}")

        # 5. Skip summary generation call to save an API call

        # 6. Save the story into the auto-created 'One-Shots' project
        project_id = self._get_or_create_oneshot_project()
        chapter_id = save_chapter(
            project_id=project_id,
            title=clean_title,
            storyline=storyline,
            content=content,
            tone=tone,
            length=length,
            summary=None,
            provider=provider_name,
            model=model_name,
            writing_profile=writing_profile
        )

        # 7. Return result
        return {
            "chapter_id": chapter_id,
            "title": clean_title,
            "content": content
        }

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
        
        # 1a. Load Relationship Memory
        relationship_memory = load_relationships(project_name)

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
            previous_summaries=context,
            relationship_memory=relationship_memory
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
