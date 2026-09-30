import os
import re
import socket
import logging
import urllib.parse
from datetime import datetime
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    func,
    inspect,
    text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError

# Load environment variables (.env)
load_dotenv(override=True)
logger = logging.getLogger(__name__)

DEFAULT_SQLITE_URL = "sqlite:///writer.db"
DB_PATH = "writer.db"

Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

class Chapter(Base):
    __tablename__ = 'chapters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    title = Column(String(255), nullable=False)
    storyline = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    tone = Column(String(100), nullable=True)
    length = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    provider = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    writing_profile = Column(String(100), nullable=True)

class StoryBible(Base):
    __tablename__ = 'story_bibles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(255), unique=True, nullable=False)
    characters = Column(Text, default='')
    relationships = Column(Text, default='')
    setting = Column(Text, default='')
    context = Column(Text, default='')
    writing_rules = Column(Text, default='')
    relationship_memory = Column(Text, default='{}')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

_engine = None
_SessionLocal = None

def resolve_supabase_host(db_url: str) -> str:
    """
    On IPv4-only networks (such as many residential ISPs and local machines),
    Supabase direct endpoints (db.<project_ref>.supabase.co) only expose IPv6 AAAA records.
    If local DNS resolution fails, this function automatically falls back to
    the Supabase IPv4-compatible Connection Pooler (aws-0-ap-southeast-1.pooler.supabase.com).
    """
    try:
        parsed = urllib.parse.urlparse(db_url)
        hostname = parsed.hostname
        if hostname and re.match(r"^db\.[a-z0-9]+\.supabase\.co$", hostname):
            port = parsed.port or 5432
            try:
                socket.getaddrinfo(hostname, port)
            except socket.gaierror:
                match = re.match(r"^db\.([a-z0-9]+)\.supabase\.co$", hostname)
                if match:
                    ref = match.group(1)
                    pooler_host = "aws-0-ap-southeast-1.pooler.supabase.com"
                    user = parsed.username or "postgres"
                    if not user.endswith(f".{ref}"):
                        user = f"{user}.{ref}"
                    password = parsed.password or ""
                    auth = f"{user}:{password}" if password else user
                    netloc = f"{auth}@{pooler_host}:{port}"
                    pooler_url = urllib.parse.urlunparse((
                        parsed.scheme,
                        netloc,
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        parsed.fragment
                    ))
                    logger.warning(
                        f"Direct Supabase host '{hostname}' could not be resolved via IPv6 DNS. "
                        f"Automatically routing to Supabase IPv4 Connection Pooler: {pooler_host}"
                    )
                    return pooler_url
    except Exception as e:
        logger.debug(f"Supabase host resolution fallback check skipped: {e}")
    return db_url

def get_database_url():
    """
    Retrieves the database connection string.
    Priority:
    1. os.environ["DATABASE_URL"] (from .env file or system env)
    2. streamlit.secrets["DATABASE_URL"] (Streamlit Cloud secrets)
    3. Fallback to local SQLite: sqlite:///writer.db
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        db_url = db_url.strip()

    # Check Streamlit Cloud secrets if not in environment
    if not db_url:
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "DATABASE_URL" in st.secrets and str(st.secrets["DATABASE_URL"]).strip():
                    db_url = str(st.secrets["DATABASE_URL"]).strip()
                elif "database" in st.secrets and "url" in st.secrets["database"] and str(st.secrets["database"]["url"]).strip():
                    db_url = str(st.secrets["database"]["url"]).strip()
                elif "postgres" in st.secrets and "url" in st.secrets["postgres"] and str(st.secrets["postgres"]["url"]).strip():
                    db_url = str(st.secrets["postgres"]["url"]).strip()
        except Exception:
            pass

    # Fallback to local SQLite if DATABASE_URL is not provided or empty
    if not db_url:
        db_url = DEFAULT_SQLITE_URL
        logger.info(f"DATABASE_URL not set or empty. Falling back to local SQLite: {db_url}")

    # SQLAlchemy compatibility: replace legacy postgres:// with postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # Automatic fallback for Supabase IPv6-only hosts on IPv4 networks
    if db_url.startswith("postgresql://") or db_url.startswith("postgresql+psycopg2://"):
        db_url = resolve_supabase_host(db_url)

    return db_url

def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        db_url = get_database_url()
        connect_args = {}

        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            _engine = create_engine(
                db_url,
                connect_args=connect_args,
                pool_pre_ping=True
            )
            logger.info(f"Connected to SQLite local database ({db_url}).")
        else:
            # PostgreSQL / Supabase
            if "sslmode" not in db_url:
                connect_args["sslmode"] = "require"
            _engine = create_engine(
                db_url,
                connect_args=connect_args,
                pool_pre_ping=True,
                pool_recycle=300
            )
            logger.info("Connected to PostgreSQL / Supabase database.")

        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine

@contextmanager
def get_session():
    get_engine()
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_db():
    """Initializes the database with required tables and handles auto-creation/migration."""
    engine = get_engine()
    Base.metadata.create_all(engine)

    # Check for legacy column migrations in existing chapters table
    try:
        inspector = inspect(engine)
        if "chapters" in inspector.get_table_names():
            existing_cols = [col["name"] for col in inspector.get_columns("chapters")]
            with engine.connect() as conn:
                for col in ["summary", "provider", "model", "writing_profile"]:
                    if col not in existing_cols:
                        conn.execute(text(f"ALTER TABLE chapters ADD COLUMN {col} TEXT"))
                conn.commit()
    except Exception as e:
        logger.warning(f"Migration check notice: {e}")

    logger.info("Database schema initialized and verified.")

def create_project(name):
    """Creates a new project in the database. Returns project ID or None if already exists."""
    try:
        with get_session() as session:
            project = Project(name=name)
            session.add(project)
            session.flush()
            return project.id
    except IntegrityError:
        return None
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return None

def get_all_projects():
    """Returns a list of all projects as tuples: [(id, name), ...] ordered by name."""
    with get_session() as session:
        projects = session.query(Project.id, Project.name).order_by(Project.name.asc()).all()
        return [(p.id, p.name) for p in projects]

def save_chapter(project_id, title, storyline, content, tone, length, summary=None, provider=None, model=None, writing_profile=None):
    """Saves a generated chapter to the database."""
    with get_session() as session:
        chapter = Chapter(
            project_id=project_id,
            title=title,
            storyline=storyline,
            content=content,
            tone=tone,
            length=length,
            summary=summary,
            provider=provider,
            model=model,
            writing_profile=writing_profile
        )
        session.add(chapter)
        session.flush()
        return chapter.id

def get_chapters_by_project(project_id):
    """Retrieves all chapters for a specific project ordered by created_at DESC."""
    with get_session() as session:
        chapters = (
            session.query(
                Chapter.id,
                Chapter.title,
                Chapter.storyline,
                Chapter.content,
                Chapter.tone,
                Chapter.length,
                Chapter.summary,
                Chapter.created_at,
                Chapter.provider,
                Chapter.model,
                Chapter.writing_profile
            )
            .filter(Chapter.project_id == project_id)
            .order_by(Chapter.created_at.desc(), Chapter.id.desc())
            .all()
        )
        return [tuple(ch) for ch in chapters]

def update_chapter_summary(chapter_id, summary):
    """Updates the summary for a specific chapter."""
    with get_session() as session:
        chapter = session.query(Chapter).filter(Chapter.id == chapter_id).first()
        if chapter:
            chapter.summary = summary

def get_latest_story_context(project_id, limit=5):
    """
    Retrieves summaries from the latest saved chapters in chronological order.
    Ignores chapters whose summary is empty or None.
    """
    with get_session() as session:
        chapters = (
            session.query(Chapter.id, Chapter.summary)
            .filter(
                Chapter.project_id == project_id,
                Chapter.summary.isnot(None),
                Chapter.summary != ""
            )
            .order_by(Chapter.id.desc())
            .limit(limit)
            .all()
        )
        chapters.reverse()
        return [ch.summary for ch in chapters]

def get_story_bible(project_name):
    """Retrieves story bible for a given project name."""
    with get_session() as session:
        bible = session.query(StoryBible).filter(StoryBible.project_name == project_name).first()
        if bible:
            return {
                "characters": bible.characters or "",
                "relationships": bible.relationships or "",
                "setting": bible.setting or "",
                "context": bible.context or "",
                "writing_rules": bible.writing_rules or ""
            }
        return None

def save_story_bible(project_name, bible_data):
    """Saves or updates the story bible for a given project name."""
    with get_session() as session:
        bible = session.query(StoryBible).filter(StoryBible.project_name == project_name).first()
        if not bible:
            bible = StoryBible(project_name=project_name)
            session.add(bible)
        bible.characters = bible_data.get("characters", "")
        bible.relationships = bible_data.get("relationships", "")
        bible.setting = bible_data.get("setting", "")
        bible.context = bible_data.get("context", "")
        bible.writing_rules = bible_data.get("writing_rules", "")

def get_relationship_memory(project_name):
    """Retrieves relationship memory dict for a given project name."""
    import json
    with get_session() as session:
        bible = session.query(StoryBible).filter(StoryBible.project_name == project_name).first()
        if bible and bible.relationship_memory:
            try:
                return json.loads(bible.relationship_memory)
            except Exception:
                return None
        return None

def save_relationship_memory(project_name, rel_data):
    """Saves or updates relationship memory for a given project name."""
    import json
    with get_session() as session:
        bible = session.query(StoryBible).filter(StoryBible.project_name == project_name).first()
        if not bible:
            bible = StoryBible(project_name=project_name)
            session.add(bible)
        bible.relationship_memory = json.dumps(rel_data, indent=4)

if __name__ == "__main__":
    init_db()
    engine = get_engine()
    print("Database initialized successfully.")
    print("Connected URL:", engine.url.render_as_string(hide_password=True))
