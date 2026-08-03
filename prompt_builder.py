from system_prompts import COMMON_WRITING_PROMPT, STANDARD_FICTION_PROFILE, MATURE_FICTION_PROFILE, ROGUE_CREATIVE_PROFILE

class PromptBuilder:
    """Constructs structured prompts for the story generation based on story context and writing profiles."""

    def __init__(self):
        self.system_instruction = (
            "You are an expert fiction author and ghostwriter. "
            "Your task is to write high-quality, engaging prose based on the provided story context."
        )

    def build_chapter_prompt(
        self,
        bible: dict,
        storyline: str,
        tone: str,
        length: str,
        writing_profile: str = "standard",
        previous_summaries: list = None
    ) -> str:
        """
        Combines all elements into a final prompt string in the specified order:
        1. Common writing prompt
        2. Selected writing profile
        3. Story Bible
        4. Previous chapter summaries
        5. Current story context
        6. User-selected tone
        7. Desired length
        8. User's rough storyline
        
        Args:
            bible (dict): Contains 'characters', 'relationships', 'setting', 'writing_rules', and optional 'context'.
            storyline (str): The specific scene or plot point to write.
            tone (str): The desired emotional or stylistic tone.
            length (str): The target length (e.g., 'short scene', 'full chapter').
            writing_profile (str): The writing profile ('standard', 'mature', or 'rogue_creative'). Defaults to 'standard'.
            previous_summaries (list): List of previous chapter summaries.
            
        Returns:
            str: The fully formatted prompt.
        """
        if not bible:
            bible = {}

        # 1. Common writing prompt
        common_prompt = COMMON_WRITING_PROMPT

        # 2. Selected writing profile
        if writing_profile == "mature":
            selected_profile = MATURE_FICTION_PROFILE
        elif writing_profile == "rogue_creative":
            selected_profile = ROGUE_CREATIVE_PROFILE
        else:
            selected_profile = STANDARD_FICTION_PROFILE

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

        # 4. Previous chapter summaries
        if previous_summaries:
            summaries_list = "\n".join(f"- {s.strip()}" for s in previous_summaries if s and s.strip())
            prev_summaries_section = f"""--- PREVIOUS CHAPTER SUMMARIES ---
{summaries_list}"""
        else:
            prev_summaries_section = """--- PREVIOUS CHAPTER SUMMARIES ---
No previous chapters."""

        # 5. Current story context
        current_context = bible.get("context", "Not defined.")
        current_context_section = f"""--- CURRENT STORY CONTEXT ---
{current_context}"""

        # 6. User-selected tone
        tone_section = f"""--- TARGET TONE ---
{tone}"""

        # 7. Desired length
        length_section = f"""--- TARGET LENGTH ---
{length}"""

        # 8. User's rough storyline
        storyline_section = f"""--- ROUGH STORYLINE / SCENE INSTRUCTION ---
{storyline}"""

        # Combine all sections in the requested order
        full_prompt = f"""
{common_prompt}

{selected_profile}

{story_bible_section}

{prev_summaries_section}

{current_context_section}

{tone_section}

{length_section}

{storyline_section}

--- TASK ---
Write the prose for this scene now. Maintain consistency with the story bible and follow the writing rules strictly. Do not include any author notes, warnings, intro/outro, or metadata. Generate only the story text in Indonesian.
"""
        return full_prompt.strip()

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
    
    test_prompt = builder.build_chapter_prompt(
        mock_bible, 
        "Elias meets Sarah in a dark alley.", 
        "Gritty Noir", 
        "Short Scene",
        writing_profile="standard",
        previous_summaries=["Elias arrived in the city.", "Sarah called him."]
    )
    print("--- GENERATED PROMPT PREVIEW ---")
    print(test_prompt)
