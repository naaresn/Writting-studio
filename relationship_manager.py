import os
import json

def get_relationship_path(project_name):
    """Returns the path to the JSON relationship memory file for a project."""
    safe_name = "".join([c for c in project_name if c.isalnum() or c in (' ', '_')]).rstrip()
    return os.path.join("projects", f"{safe_name}_relationships.json")

def load_relationships(project_name):
    """Loads the relationship memory from a JSON file."""
    path = get_relationship_path(project_name)
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            # Ensure all required fields exist with default values if loading old format
            default_structure = {
                "running_gags": {"content": "", "priority": "Medium"},
                "habits": {"content": "", "priority": "Medium"},
                "love_languages": {"content": "", "priority": "Medium"},
                "comfort_behaviors": {"content": "", "priority": "Medium"},
                "inside_jokes": {"content": "", "priority": "Medium"},
                "daily_rituals": {"content": "", "priority": "Medium"},
                "nicknames": {"content": "", "priority": "Medium"},
                "pet_peeves": {"content": "", "priority": "Medium"},
                "shared_memories": {"content": "", "priority": "Medium"},
                "relationship_evolution": {"content": "", "priority": "Medium"}
            }
            # Update with loaded data
            for key in default_structure:
                if key not in data:
                    data[key] = default_structure[key]
                elif isinstance(data[key], list):
                    # Migration: convert list to new dict structure
                    data[key] = {"content": "\n".join(data[key]), "priority": "Medium"}
            return data
    # Return default structure if not found
    return {
        "running_gags": {"content": "", "priority": "Medium"},
        "habits": {"content": "", "priority": "Medium"},
        "love_languages": {"content": "", "priority": "Medium"},
        "comfort_behaviors": {"content": "", "priority": "Medium"},
        "inside_jokes": {"content": "", "priority": "Medium"},
        "daily_rituals": {"content": "", "priority": "Medium"},
        "nicknames": {"content": "", "priority": "Medium"},
        "pet_peeves": {"content": "", "priority": "Medium"},
        "shared_memories": {"content": "", "priority": "Medium"},
        "relationship_evolution": {"content": "", "priority": "Medium"}
    }

def save_relationships(project_name, relationship_data):
    """Saves the relationship memory to a JSON file."""
    os.makedirs("projects", exist_ok=True)
    path = get_relationship_path(project_name)
    with open(path, "w") as f:
        json.dump(relationship_data, f, indent=4)
