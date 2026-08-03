import streamlit as st
import database
import bible_manager
from story_service import StoryService
import os

# Initialize database
database.init_db()

# Page configuration
st.set_page_config(page_title="Story Studio", layout="wide")
st.title("Story Studio")

# Sidebar: Project Management
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
        
        if st.button("Save Bible"):
            new_bible = {
                "characters": characters,
                "relationships": relationships,
                "setting": setting,
                "context": context,
                "writing_rules": style
            }
            bible_manager.save_bible(selected_project_name, new_bible)
            st.success("Story Bible saved!")

    # TAB 2: Writing Room
    with tab2:
        st.header("Writing Room")
        
        col1, col2 = st.columns(2)
        with col1:
            chapter_title = st.text_input("Chapter Title")
            tone = st.selectbox("Tone", ["Soft Romantic", "Comedy", "Angst", "Dark", "Fantasy", "Slice of Life", "Custom"])
            length = st.selectbox("Length", ["Short Scene", "Medium Scene", "Long Chapter"])
        
        with col2:
            provider = st.selectbox("AI Provider", ["Gemini", "Qwen Local"])
            
            # Map UI labels to backend values
            provider_map = {"Gemini": "gemini", "Qwen Local": "qwen"}
            selected_provider_key = provider_map[provider]
            
            profile = "standard"
            if selected_provider_key == "qwen":
                profile_option = st.selectbox("Writing Profile", ["Standard Fiction", "Mature Fiction (18+)"])
                st.caption("For fictional consenting adult characters only.")
                if profile_option == "Mature Fiction (18+)":
                    profile = "mature"
            else:
                st.write("Profile: Standard Fiction")
        
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
                # ch is (id, title, storyline, content, tone, length, summary, created_at, provider, model, writing_profile)
                # indices: 0:id, 1:title, 2:storyline, 3:content, 4:tone, 5:length, 6:summary, 7:created_at, 8:provider, 9:model, 10:writing_profile
                with st.expander(f"{ch[1]} - {ch[7]}"):
                    st.write(f"**Storyline:** {ch[2]}")
                    st.write(f"**Tone:** {ch[4]}")
                    st.write(f"**Length:** {ch[5]}")
                    st.write(f"**Provider:** {ch[8] or 'N/A'} ({ch[9] or 'N/A'}) - **Profile:** {ch[10] or 'N/A'}")
                    st.text_area("Content", value=ch[3], height=300, disabled=True)
                    st.write(f"**Summary:**")
                    st.write(ch[6])

else:
    st.info("Please select or create a project in the sidebar.")
