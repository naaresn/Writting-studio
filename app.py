import streamlit as st
from dotenv import load_dotenv
import database
import bible_manager
import relationship_manager
from story_service import StoryService
import os
import logging

# Load environment variables once at startup
load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
database.init_db()

# Page configuration
st.set_page_config(page_title="Story Studio", layout="wide")
st.title("Story Studio")

# Shared options and mappings
TONE_OPTIONS = ["Soft Romantic", "Comedy", "Angst", "Dark", "Fantasy", "Slice of Life", "Custom"]
LENGTH_OPTIONS = ["Short Scene", "Medium Scene", "Long Chapter"]
PROVIDER_OPTIONS = ["Gemini", "OpenRouter (Qwen)", "Qwen Local", "Gemma Creative"]
PROVIDER_MAP = {
    "Gemini": "Gemini",
    "OpenRouter (Qwen)": "OpenRouter (Qwen)",
    "Qwen Local": "Qwen Local",
    "Gemma Creative": "Gemma Creative"
}

def render_provider_and_profile_controls(key_prefix: str):
    """
    Renders AI Provider and Writing Profile selectors.
    Returns (selected_provider_key, writing_profile).
    """
    provider = st.selectbox("AI Provider", PROVIDER_OPTIONS, key=f"{key_prefix}_provider")
    selected_provider_key = PROVIDER_MAP[provider]

    profile = "standard"
    if selected_provider_key == "Qwen Local":
        profile_option = st.selectbox(
            "Writing Profile",
            ["Standard Fiction", "Mature Fiction (18+)"],
            key=f"{key_prefix}_profile"
        )
        st.caption("For fictional consenting adult characters only.")
        if profile_option == "Mature Fiction (18+)":
            profile = "mature"
    elif selected_provider_key == "OpenRouter (Qwen)":
        profile_option = st.selectbox(
            "Writing Profile",
            ["Standard Fiction", "Mature Fiction (18+)"],
            key=f"{key_prefix}_profile"
        )
        st.caption("Powered by OpenRouter API (Qwen model).")
        if profile_option == "Mature Fiction (18+)":
            profile = "mature"
    elif selected_provider_key == "Gemma Creative":
        profile = "gemma_creative"
        st.write("Profile: Gemma Creative (Optimized for long-form fiction)")
    else:
        st.write("Profile: Standard Fiction")

    return selected_provider_key, profile

# Sidebar: Navigation Mode Switch
app_mode = st.sidebar.radio("Mode", ["One-Shot", "Projects"], index=0)

if app_mode == "One-Shot":
    st.sidebar.markdown("---")
    st.sidebar.info("One-Shot mode creates complete standalone stories without requiring a Story Bible or project configuration. Generated stories are saved into the 'One-Shots' project.")

    st.header("One-Shot Story Generator")
    st.caption("Generate a complete, self-contained story with just a rough storyline.")

    col1, col2 = st.columns(2)
    with col1:
        oneshot_title = st.text_input("Story Title (Optional)", placeholder="Leave blank to auto-generate from storyline", key="oneshot_title")
        tone = st.selectbox("Tone", TONE_OPTIONS, key="oneshot_tone")
        length = st.selectbox("Length", LENGTH_OPTIONS, key="oneshot_length")

    with col2:
        selected_provider_key, profile = render_provider_and_profile_controls(key_prefix="oneshot")

    storyline = st.text_area("Rough storyline", height=200, placeholder="Describe the storyline or scene idea here...", key="oneshot_storyline")

    if st.button("Generate Story", key="oneshot_generate_btn"):
        if not storyline or not storyline.strip():
            st.error("Please provide a storyline.")
        else:
            try:
                with st.spinner("Generating story..."):
                    service = StoryService()
                    result = service.generate_oneshot(
                        storyline=storyline.strip(),
                        tone=tone,
                        length=length,
                        provider_name=selected_provider_key,
                        writing_profile=profile,
                        title=oneshot_title.strip() if oneshot_title else None
                    )
                st.session_state["oneshot_result"] = result
                st.success(f"Story generated and saved! Title: '{result['title']}' (Chapter ID: {result['chapter_id']})")
            except Exception as e:
                logger.error(f"Error generating one-shot story: {e}")
                st.error(f"Error generating story: {e}")

    # Display generated story from session state
    if "oneshot_result" in st.session_state and st.session_state["oneshot_result"]:
        result = st.session_state["oneshot_result"]
        st.subheader(f"Generated Story: {result.get('title', 'Untitled')}")
        st.text_area("Generated Content", value=result.get("content", ""), height=400, key="oneshot_content_display")

        safe_filename = "".join(c for c in result.get("title", "oneshot_story") if c.isalnum() or c in (' ', '_', '-')).strip()
        if not safe_filename:
            safe_filename = "oneshot_story"

        st.download_button(
            label="Download Story (.txt)",
            data=result.get("content", ""),
            file_name=f"{safe_filename}.txt",
            mime="text/plain",
            key="oneshot_download_btn"
        )

else:
    # Sidebar: Project Management
    st.sidebar.markdown("---")
    st.sidebar.header("Project Management")

    # Project selection
    projects = database.get_all_projects()
    project_options = {p[1]: p[0] for p in projects}
    selected_project_name = st.sidebar.selectbox("Select Project", [""] + list(project_options.keys()))

    # Create new project
    with st.sidebar.expander("Create New Project"):
        new_project_name = st.text_input("New Project Name")
        if st.button("Create"):
            if not new_project_name:
                st.error("Project name cannot be empty.")
            elif new_project_name in project_options:
                st.error("Project already exists.")
            else:
                database.create_project(new_project_name)
                st.success(f"Project '{new_project_name}' created.")
                st.rerun()

    # Display selected project info
    if selected_project_name:
        project_id = project_options[selected_project_name]
        st.sidebar.info(f"Selected: {selected_project_name} (ID: {project_id})")

        # Main interface with tabs
        tab1, tab2, tab3 = st.tabs(["Story Bible", "Writing Room", "Chapter Library"])

        # TAB 1: Story Bible
        with tab1:
            st.header("Story Bible")
            bible_data = bible_manager.load_bible(selected_project_name)
            
            # Editable fields
            characters = st.text_area("Characters", value=bible_data.get("characters", ""), height=150)
            relationships = st.text_area("Relationships", value=bible_data.get("relationships", ""), height=100)
            setting = st.text_area("Setting and world information", value=bible_data.get("setting", ""), height=150)
            context = st.text_area("Current story context", value=bible_data.get("context", ""), height=100)
            style = st.text_area("Writing style and rules", value=bible_data.get("writing_rules", ""), height=100)
            
            # Relationship Memory
            st.subheader("Relationship Memory")
            rel_data = relationship_manager.load_relationships(selected_project_name)
            rel_inputs = {}
            
            with st.expander("Manage Relationship Memory"):
                fields = [
                    ("running_gags", "Running Gags"),
                    ("habits", "Habits"),
                    ("love_languages", "Love Languages"),
                    ("comfort_behaviors", "Comfort Behaviors"),
                    ("inside_jokes", "Inside Jokes"),
                    ("daily_rituals", "Daily Rituals"),
                    ("nicknames", "Nicknames"),
                    ("pet_peeves", "Pet Peeves"),
                    ("shared_memories", "Shared Memories"),
                    ("relationship_evolution", "Relationship Evolution")
                ]
                
                for key, label in fields:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        content = st.text_area(label, value=rel_data[key].get("content", ""), key=f"{project_id}_{key}_content")
                    with col2:
                        priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(rel_data[key].get("priority", "Medium")), key=f"{project_id}_{key}_priority")
                    rel_inputs[key] = {"content": content, "priority": priority}

            if st.button("Save Bible"):
                new_bible = {
                    "characters": characters,
                    "relationships": relationships,
                    "setting": setting,
                    "context": context,
                    "writing_rules": style
                }
                bible_manager.save_bible(selected_project_name, new_bible)
                relationship_manager.save_relationships(selected_project_name, rel_inputs)
                st.success("Story Bible and Relationship Memory saved!")

        # TAB 2: Writing Room
        with tab2:
            st.header("Writing Room")
            
            col1, col2 = st.columns(2)
            with col1:
                chapter_title = st.text_input("Chapter Title")
                tone = st.selectbox("Tone", TONE_OPTIONS, key="writing_room_tone")
                length = st.selectbox("Length", LENGTH_OPTIONS, key="writing_room_length")
            
            with col2:
                selected_provider_key, profile = render_provider_and_profile_controls(key_prefix="writing_room")
            
            storyline = st.text_area("Rough storyline or scene instruction", height=200)
            
            if st.button("Generate Chapter"):
                if not chapter_title or not storyline:
                    st.error("Please provide both a title and storyline.")
                else:
                    try:
                        with st.spinner("Generating..."):
                            service = StoryService()
                            result = service.generate_chapter(
                                project_id, selected_project_name, chapter_title, storyline, tone, length,
                                provider_name=selected_provider_key,
                                writing_profile=profile
                            )
                        st.success("Chapter generated and saved!")
                        st.write(f"Chapter ID: {result['chapter_id']}")
                        st.text_area("Generated Content", value=result['content'], height=400)
                        with st.expander("Generated Summary"):
                            st.write(result['summary'])
                    except Exception as e:
                        st.error(f"Error generating chapter: {e}")

        # TAB 3: Chapter Library
        with tab3:
            st.header("Chapter Library")
            chapters = database.get_chapters_by_project(project_id)
            
            if not chapters:
                st.write("No chapters created for this project yet.")
            else:
                for ch in chapters:
                    with st.expander(f"{ch[1]} - {ch[7]}"):
                        st.write(f"**Storyline:** {ch[2]}")
                        st.write(f"**Tone:** {ch[4]}")
                        st.write(f"**Length:** {ch[5]}")
                        st.write(f"**Provider:** {ch[8] or 'N/A'} ({ch[9] or 'N/A'}) - **Profile:** {ch[10] or 'N/A'}")
                        st.text_area("Content", value=ch[3], height=300, disabled=True, key=f"library_content_{ch[0]}")
                        st.write(f"**Summary:**")
                        st.write(ch[6] or "No summary.")

    else:
        st.info("Please select or create a project in the sidebar.")
