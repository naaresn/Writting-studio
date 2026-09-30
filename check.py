import os
import glob
import json
import sqlite3

conn = sqlite3.connect("data/story_studio.db")
cur = conn.cursor()
cur.execute("SELECT id, name FROM projects")
projects = cur.fetchall()
conn.close()

def get_bible_path(project_name):
    safe_name = "".join([c for c in project_name if c.isalnum() or c in (' ', '_')]).rstrip()
    return os.path.join("projects", f"{safe_name}_bible.json")

def get_relationship_path(project_name):
    safe_name = "".join([c for c in project_name if c.isalnum() or c in (' ', '_')]).rstrip()
    return os.path.join("projects", f"{safe_name}_relationships.json")

print("Project mappings to JSON files:")
for pid, pname in projects:
    bpath = get_bible_path(pname)
    rpath = get_relationship_path(pname)
    print(f"Project [{pname}]:")
    print(f"  Bible exists: {os.path.exists(bpath)} ({bpath})")
    print(f"  Rel exists: {os.path.exists(rpath)} ({rpath})")
    if os.path.exists(bpath):
        with open(bpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"    Bible keys: {list(data.keys())}")
