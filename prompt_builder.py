from system_prompts import COMMON_WRITING_PROMPT, OLLAMA_INDONESIAN_ROMANCE_PROMPT, STANDARD_FICTION_PROFILE, MATURE_FICTION_PROFILE, GEMMA_CREATIVE_PROFILE
from mature_fiction_prompt import MATURE_FICTION_MODULE

class PromptBuilder:
    """Constructs structured prompts for the story generation based on story context and writing profiles."""

    def __init__(self):
        self.system_instruction = (
            "You are an expert fiction author and ghostwriter. "
            "Your task is to write high-quality, engaging prose based on the provided story context."
        )

    def build_chapter_prompt(
        self,
        bible: dict = None,
        storyline: str = "",
        tone: str = "",
        length: str = "",
        writing_profile: str = "standard",
        previous_summaries: list = None,
        provider_type: str = "gemini",
        relationship_memory: dict = None,
        mode: str = "chapter"
    ) -> str:
        """
        Combines all elements into a final prompt string.
        
        Args:
            bible (dict): Contains 'characters', 'relationships', 'setting', 'writing_rules', and optional 'context'.
            storyline (str): The specific scene or plot point to write.
            tone (str): The desired emotional or stylistic tone.
            length (str): The target length (e.g., 'short scene', 'full chapter').
            writing_profile (str): The writing profile ('standard', 'mature', or 'gemma_creative'). Defaults to 'standard'.
            previous_summaries (list): List of previous chapter summaries.
            provider_type (str): 'gemini' or 'ollama'.
            relationship_memory (dict): Optional dictionary of relationship memories (running_gags, habits, etc.)
            mode (str): 'chapter' (default) or 'oneshot'.
            
        Returns:
            str: The fully formatted prompt.
        """
        if not bible:
            bible = {}

        # 1. Common writing prompt / Ollama prompt
        if provider_type == "ollama":
            base_prompt = OLLAMA_INDONESIAN_ROMANCE_PROMPT
        else:
            base_prompt = COMMON_WRITING_PROMPT

        # 2. Selected writing profile
        mature_module = ""
        if writing_profile == "mature":
            selected_profile = MATURE_FICTION_PROFILE
            mature_module = f"\n\n{MATURE_FICTION_MODULE}"
        elif writing_profile == "gemma_creative":
            selected_profile = GEMMA_CREATIVE_PROFILE
        else:
            selected_profile = STANDARD_FICTION_PROFILE

        # Determine if a non-empty story bible is provided
        has_bible = any(isinstance(v, str) and v.strip() for v in bible.values()) if bible else False

        sections = [base_prompt]
        if mature_module:
            sections.append(f"{selected_profile}{mature_module}")
        else:
            sections.append(selected_profile)

        # Omit Story Bible, Relationship Memory, Previous Summaries, and Context if bible is empty/undefined
        if has_bible:
            # 3. Story Bible
            characters = bible.get("characters", "Not defined.")
            relationships = bible.get("relationships", "Not defined.")
            setting = bible.get("setting", "Not defined.")
            rules = bible.get("writing_rules", "Follow standard fiction writing best practices.")

            story_bible_section = f"""--- STORY BIBLE ---
CHARACTERS:
{characters}

RELATIONSHIPS:
{relationships}

WORLD SETTING:
{setting}

WRITING RULES:
{rules}"""
            sections.append(story_bible_section)

            # 4. Relationship Memory
            if relationship_memory:
                formatted_memories = []
                for category, data in relationship_memory.items():
                    content = data.get("content", "").strip()
                    priority = data.get("priority", "Medium")
                    if content:
                        category_name = category.replace("_", " ").title()
                        formatted_memories.append(f"{category_name} (Priority: {priority}):\n{content}")
                
                if formatted_memories:
                    relationship_section = f"""--- RELATIONSHIP MEMORY ---
{chr(10).join(formatted_memories)}"""
                else:
                    relationship_section = "--- RELATIONSHIP MEMORY ---\nNo specific relationship memories defined yet."
            else:
                relationship_section = "--- RELATIONSHIP MEMORY ---\nNo specific relationship memories defined yet."
            sections.append(relationship_section)

            # 5. Previous chapter summaries
            if previous_summaries:
                summaries_list = "\n".join(f"- {s.strip()}" for s in previous_summaries if s and s.strip())
                prev_summaries_section = f"""--- PREVIOUS CHAPTER SUMMARIES ---
{summaries_list}"""
            else:
                prev_summaries_section = """--- PREVIOUS CHAPTER SUMMARIES ---
No previous chapters."""
            sections.append(prev_summaries_section)

            # 6. Current story context
            current_context = bible.get("context", "Not defined.")
            current_context_section = f"""--- CURRENT STORY CONTEXT ---
{current_context}"""
            sections.append(current_context_section)

        # 7. User-selected tone
        tone_section = f"""--- TARGET TONE ---
{tone}"""
        sections.append(tone_section)

        # 8. Desired length
        length_section = f"""--- TARGET LENGTH ---
{length}"""
        sections.append(length_section)

        # 9. User's rough storyline
        storyline_section = f"""--- ROUGH STORYLINE / SCENE INSTRUCTION ---
{storyline}"""
        sections.append(storyline_section)

        # 10. Task instruction
        if mode == "oneshot":
            task_instruction = (
                "Write a complete, self-contained story with a clear beginning, development, and ending based on the storyline. "
                "Invent any needed character details consistently from the storyline. "
                "Do not include any author notes, warnings, intro/outro, or metadata. "
                "Generate only the story text in Indonesian."
            )
        else:
            task_instruction = (
                "Write the prose for this scene now. Maintain consistency with the story bible and follow the writing rules strictly. "
                "Do not include any author notes, warnings, intro/outro, or metadata. "
                "Generate only the story text in Indonesian."
            )

        task_section = f"""--- TASK ---
{task_instruction}"""
        sections.append(task_section)

        return "\n\n".join(sections).strip()

if __name__ == "__main__":
    # Quick test
    builder = PromptBuilder()
    mock_bible = {
        "characters": "Elias: A weary detective. Sarah: A mysterious informant.",
        "relationships": "Elias distrusts Sarah.",
        "setting": "A rain-slicked city in 2049.",
        "writing_rules": "Use sensory details. Show, don't tell.",
        "context": "They have just met in a coffee shop."
    }
    
    # Test Gemini prompt
    test_prompt = builder.build_chapter_prompt(
        mock_bible, 
        "Elias meets Sarah in a dark alley.", 
        "Gritty Noir", 
        "Short Scene",
        writing_profile="standard",
        previous_summaries=["Elias arrived in the city.", "Sarah called him."],
        provider_type="gemini"
    )
    print("--- GENERATED GEMINI PROMPT PREVIEW ---")
    print(test_prompt)
    
    # Test Ollama prompt
    test_prompt_ollama = builder.build_chapter_prompt(
        mock_bible, 
        "Elias meets Sarah in a dark alley.", 
        "Gritty Noir", 
        "Short Scene",
        writing_profile="standard",
        previous_summaries=["Elias arrived in the city.", "Sarah called him."],
        provider_type="ollama"
    )
    print("\n--- GENERATED OLLAMA PROMPT PREVIEW ---")
    print(test_prompt_ollama)
