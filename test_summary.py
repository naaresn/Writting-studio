import os
from dotenv import load_dotenv
from summary_builder import SummaryBuilder
from provider_factory import get_ai_provider

def run_test():
    load_dotenv()
    
    # 1. Sample Indonesian Chapter
    sample_chapter = """
    Aksara menatap layar komputernya dengan lelah, ketika tiba-tiba Karina masuk ke ruangannya. Karina tersenyum lebar, membawa sekotak makan siang favorit Aksara. 
    "Aku tahu kamu belum makan," kata Karina sambil meletakkan kotak itu di meja.
    Aksara awalnya merasa terganggu, namun melihat senyum tulus Karina, hatinya luluh. Ia menutup laptopnya dan menatap Karina. 
    "Terima kasih, Karina. Aku memang lapar sekali," jawab Aksara lembut.
    Mereka akhirnya makan siang bersama, saling tertawa dan bercerita tentang hari mereka. Suasana kantor yang tadinya tegang menjadi hangat dan penuh tawa.
    Bab berakhir dengan Aksara yang merasa jauh lebih tenang dan bahagia setelah kehadiran Karina.
    """
    
    print("--- Testing Summary Builder ---")
    
    # 2. Build Summary Prompt
    builder = SummaryBuilder()
    prompt = builder.build_summary_prompt(sample_chapter)
    
    print("\n--- PROMPT PREVIEW ---")
    print(prompt)
    
    # 3. Generate Summary
    try:
        print("\n--- GENERATING SUMMARY (Please wait...) ---")
        provider = get_ai_provider()
        summary = provider.generate(prompt)
        
        print("\n--- GENERATED SUMMARY ---")
        print(summary)
        print("\n--- TEST COMPLETE ---")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")

if __name__ == "__main__":
    run_test()
