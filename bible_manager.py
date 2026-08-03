import os
import json

def get_bible_path(project_name):
    """Returns the path to the JSON bible file for a project."""
    # Ensure filename is safe
    safe_name = "".join([c for c in project_name if c.isalnum() or c in (' ', '_')]).rstrip()
    return os.path.join("projects", f"{safe_name}_bible.json")

def load_bible(project_name):
    """Loads the story bible from a JSON file."""
    path = get_bible_path(project_name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {
        "characters": "",
        "relationships": "",
        "setting": "",
        "writing_rules": ""
    }

def save_bible(project_name, bible_data):
    """Saves the story bible to a JSON file."""
    os.makedirs("projects", exist_ok=True)
    path = get_bible_path(project_name)
    with open(path, "w") as f:
        json.dump(bible_data, f, indent=4)
