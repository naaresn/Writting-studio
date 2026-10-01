import pytest
from unittest.mock import MagicMock, patch
import database
from prompt_builder import PromptBuilder
from story_service import StoryService

@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Initializes a fresh isolated SQLite database for each test."""
    db_file = tmp_path / "test_writer.db"
    db_url = f"sqlite:///{db_file}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    
    # Reset cached database engines
    database._engine = None
    database._SessionLocal = None
    database.init_db()
    yield
    database._engine = None
    database._SessionLocal = None

class TestPromptBuilderOneShot:
    def test_prompt_builder_oneshot_omits_empty_sections(self):
        builder = PromptBuilder()
        prompt = builder.build_chapter_prompt(
            bible={},
            storyline="Aksara bertemu Karina di taman bunga pada sore hari.",
            tone="Soft Romantic",
            length="Short Scene",
            mode="oneshot"
        )

        # Omitted sections check
        assert "--- STORY BIBLE ---" not in prompt
        assert "--- RELATIONSHIP MEMORY ---" not in prompt
        assert "--- PREVIOUS CHAPTER SUMMARIES ---" not in prompt
        assert "--- CURRENT STORY CONTEXT ---" not in prompt
        assert "Not defined." not in prompt
        assert "No previous chapters." not in prompt

        # Included sections check
        assert "--- TARGET TONE ---" in prompt
        assert "Soft Romantic" in prompt
        assert "--- TARGET LENGTH ---" in prompt
        assert "Short Scene" in prompt
        assert "--- ROUGH STORYLINE / SCENE INSTRUCTION ---" in prompt
        assert "Aksara bertemu Karina di taman bunga pada sore hari." in prompt
        assert "--- TASK ---" in prompt

        # Task instruction check for oneshot mode
        assert "complete, self-contained story" in prompt
        assert "clear beginning, development, and ending" in prompt
        assert "Invent any needed character details consistently" in prompt
        assert "Generate only the story text in Indonesian." in prompt

    def test_prompt_builder_chapter_with_bible_preserved(self):
        builder = PromptBuilder()
        sample_bible = {
            "characters": "Aksara: Penulis. Karina: Editor.",
            "relationships": "Rekan kerja yang saling menyukai.",
            "setting": "Jakarta, 2026.",
            "writing_rules": "Gunakan gaya bahasa santai tapi hangat.",
            "context": "Mereka baru saja menyelesaikan naskah pertama."
        }
        summaries = ["Bab 1: Pertemuan pertama di kafe."]

        prompt = builder.build_chapter_prompt(
            bible=sample_bible,
            storyline="Aksara mengajak Karina makan malam untuk merayakan.",
            tone="Warm",
            length="Short Scene",
            previous_summaries=summaries,
            mode="chapter"
        )

        assert "--- STORY BIBLE ---" in prompt
        assert "Aksara: Penulis. Karina: Editor." in prompt
        assert "--- RELATIONSHIP MEMORY ---" in prompt
        assert "--- PREVIOUS CHAPTER SUMMARIES ---" in prompt
        assert "Bab 1: Pertemuan pertama di kafe." in prompt
        assert "--- CURRENT STORY CONTEXT ---" in prompt
        assert "Mereka baru saja menyelesaikan naskah pertama." in prompt
        assert "Write the prose for this scene now. Maintain consistency with the story bible" in prompt

class TestStoryServiceOneShot:
    def test_generate_oneshot_success(self):
        service = StoryService()
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        mock_provider.generate.return_value = "Ini adalah cerita one-shot yang lengkap dan mandiri."

        with patch("story_service.get_ai_provider", return_value=mock_provider):
            result = service.generate_oneshot(
                storyline="Aksara dan Karina berjalan menyusuri pantai saat matahari terbenam.",
                tone="Soft Romantic",
                length="Short Scene",
                title="Senja di Pantai",
                provider_name="gemini",
                writing_profile="standard"
            )

        # Provider generate should be called exactly once (no summary generation call)
        assert mock_provider.generate.call_count == 1

        # Check return structure
        assert isinstance(result, dict)
        assert "chapter_id" in result
        assert result["title"] == "Senja di Pantai"
        assert result["content"] == "Ini adalah cerita one-shot yang lengkap dan mandiri."
        assert result["chapter_id"] is not None

        # Verify it was saved to the 'One-Shots' project
        projects = database.get_all_projects()
        oneshot_proj = next((p for p in projects if p[1] == "One-Shots"), None)
        assert oneshot_proj is not None

        chapters = database.get_chapters_by_project(oneshot_proj[0])
        assert len(chapters) == 1
        assert chapters[0][1] == "Senja di Pantai"
        assert chapters[0][3] == "Ini adalah cerita one-shot yang lengkap dan mandiri."
        assert chapters[0][6] is None  # summary is None for one-shots

    def test_generate_oneshot_title_derivation(self):
        service = StoryService()
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        mock_provider.generate.return_value = "Story text"

        with patch("story_service.get_ai_provider", return_value=mock_provider):
            # Storyline with >6 words
            res1 = service.generate_oneshot(
                storyline="Satu dua tiga empat lima enam tujuh delapan sembilan",
                tone="Comedy",
                length="Short Scene",
                title=None
            )
            assert res1["title"] == "Satu dua tiga empat lima enam"

            # Storyline with <=6 words
            res2 = service.generate_oneshot(
                storyline="Hujan di sore hari",
                tone="Slice of Life",
                length="Short Scene",
                title=""
            )
            assert res2["title"] == "Hujan di sore hari"

            # Empty storyline fallback
            res3 = service.generate_oneshot(
                storyline="",
                tone="Dark",
                length="Short Scene",
                title="   "
            )
            assert res3["title"] == "Untitled One-Shot"

    def test_oneshot_project_created_once_and_reused(self):
        service = StoryService()
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        mock_provider.generate.return_value = "Story content"

        with patch("story_service.get_ai_provider", return_value=mock_provider):
            res1 = service.generate_oneshot(
                storyline="Kisah pertama",
                tone="Fantasy",
                length="Short Scene",
                title="Kisah 1"
            )
            res2 = service.generate_oneshot(
                storyline="Kisah kedua",
                tone="Fantasy",
                length="Short Scene",
                title="Kisah 2"
            )

        projects = database.get_all_projects()
        oneshot_projects = [p for p in projects if p[1] == "One-Shots"]
        # Must be created once and only once
        assert len(oneshot_projects) == 1

        oneshot_proj_id = oneshot_projects[0][0]
        chapters = database.get_chapters_by_project(oneshot_proj_id)
        # Both stories must be saved under this single project
        assert len(chapters) == 2
        titles = [ch[1] for ch in chapters]
        assert "Kisah 1" in titles
        assert "Kisah 2" in titles

    def test_generate_oneshot_provider_error(self):
        service = StoryService()
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = RuntimeError("API connection timeout")

        with patch("story_service.get_ai_provider", return_value=mock_provider):
            with pytest.raises(Exception) as exc_info:
                service.generate_oneshot(
                    storyline="Sebuah cerita yang gagal di-generate",
                    tone="Angst",
                    length="Short Scene"
                )
            assert "Story generation failed" in str(exc_info.value)
