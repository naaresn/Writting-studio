from prompt_builder import PromptBuilder

def run_test():
    builder = PromptBuilder()
    
    mock_bible = {
        "characters": "Elias: A weary detective. Sarah: A mysterious informant.",
        "relationships": "Elias distrusts Sarah.",
        "setting": "A rain-slicked city in 2049.",
        "writing_rules": "Use sensory details. Show, don't tell.",
        "context": "They have just met in a coffee shop."
    }
    
    storyline = "Elias meets Sarah in a dark alley."
    tone = "Gritty Noir"
    length = "Short Scene"
    previous_summaries = ["Elias arrived in the city.", "Sarah called him."]

    test_cases = [
        ("Gemini", "standard", "standard"),
        ("Qwen", "standard", "standard"),
        ("Qwen", "mature", "mature"),
    ]

    for provider, profile_label, profile_key in test_cases:
        print(f"\n{'='*20}")
        print(f"TEST CASE: {provider} + {profile_label} profile")
        print(f"{'='*20}")
        
        prompt = builder.build_chapter_prompt(
            bible=mock_bible,
            storyline=storyline,
            tone=tone,
            length=length,
            writing_profile=profile_key,
            previous_summaries=previous_summaries
        )
        
        # Verify no API keys (just a simple check)
        if "GEMINI_API_KEY" in prompt:
            print("ERROR: API Key leaked in prompt!")
            return
            
        print(prompt)

if __name__ == "__main__":
    run_test()
