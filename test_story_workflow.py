import os
from database import init_db, create_project, get_all_projects
from bible_manager import save_bible
from story_service import StoryService

def run_test():
    # 1. Initialize the database
    init_db()
    print("Database initialized.")

    # 2. Create or retrieve a sample project
    project_name = "Sample Story"
    projects = get_all_projects()
    project = next((p for p in projects if p[1] == project_name), None)
    
    if project:
        project_id = project[0]
        print(f"Using existing project: {project_name} (ID: {project_id})")
    else:
        project_id = create_project(project_name)
        print(f"Created new project: {project_name} (ID: {project_id})")

    # 3. Ensure a sample Story Bible exists
    sample_bible = {
        "characters": "John: A brave knight.",
        "relationships": "John loves Mary.",
        "setting": "A medieval kingdom.",
        "writing_rules": "Use vivid imagery."
    }
    save_bible(project_name, sample_bible)
    print("Sample Story Bible saved.")

    # 4. Generate one chapter using StoryService
    service = StoryService()
    print("Generating chapter...")
    result = service.generate_chapter(
        project_id=project_id,
        project_name=project_name,
        title="Chapter 1: The Adventure Begins",
        storyline="John goes into the forest to find the dragon.",
        tone="Exciting",
        length="500 words"
    )

    # 5. Print the generated chapter, summary, and saved chapter ID
    print("\n--- TEST RESULTS ---")
    print(f"Chapter ID: {result['chapter_id']}")
    print(f"\n--- SUMMARY ---\n{result['summary']}")
    print(f"\n--- CONTENT (preview) ---\n{result['content'][:500]}...")

if __name__ == "__main__":
    run_test()
    print("\nTo run this test, use the command: python test_story_workflow.py")
