import os
import json
from bible_manager import load_bible
from prompt_builder import PromptBuilder
from provider_factory import get_ai_provider

def run_test():
    
    # 2. Check for API Key (specific to Gemini for this test)
    provider_name = os.getenv("AI_PROVIDER", "gemini")
    if provider_name == "gemini" and not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY is not set in .env")
        print("Please copy .env.example to .env and add your key.")
        return

    print(f"--- Starting End-to-End Test (Provider: {provider_name}) ---")

    # 3. Load Sample Bible
    # Since bible_manager expects project_name, we use 'sample'
    bible = load_bible("sample")
    
    # 4. Define Test Parameters
    storyline = (
        "Aksara sedang bekerja di kantornya. Karina datang membawa makan siang karena rindu. "
        "Awalnya ia duduk tenang, lalu mulai mengganggu Aksara. "
        "Buat adegannya lembut, romantis, dan sedikit lucu."
    )
    tone = "Lembut, Romantis, Sedikit Lucu"
    length = "Scene Pendek"
    
    # 5. Build the Prompt
    builder = PromptBuilder()
    final_prompt = builder.build_chapter_prompt(bible, storyline, tone, length)
    
    print("\n--- FINAL PROMPT PREVIEW ---")
    print(final_prompt[:300] + "...") # Show just the start for brevity
    
    # 6. Initialize AI Provider and Generate
    try:
        print("\n--- GENERATING STORY (Please wait...) ---")
        provider = get_ai_provider()
        generated_story = provider.generate(final_prompt)
        
        print("\n--- GENERATED STORY ---")
        print(generated_story)
        print("\n--- TEST COMPLETE ---")
        
    except Exception as e:
        print(f"\nFATAL ERROR during generation: {str(e)}")

if __name__ == "__main__":
    run_test()
