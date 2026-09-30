#!/usr/bin/env python3
"""
migrate_sqlite_to_supabase.py
=============================
Skrip migrasi data dari SQLite lokal ke database Supabase PostgreSQL.

Fitur:
1. Membaca data Projects, Chapters, dan Story Bibles dari SQLite lokal.
2. Membaca Story Bible & Relationship Memory dari folder `projects/*.json`
   (fallback otomatis jika tabel story_bibles di SQLite kosong).
3. Mencegah duplikasi data jika skrip dijalankan berulang kali (Idempotent).
4. Menyelaraskan sequence autoincrement ID di PostgreSQL Supabase.
5. Mendukung flag `--dry-run` untuk simulasi tanpa mengubah data.
6. Auto-detect file SQLite lokal (story_studio.db, writer.db, database.db, dll.).

Penggunaan:
    python migrate_sqlite_to_supabase.py
    python migrate_sqlite_to_supabase.py --sqlite data/story_studio.db
    python migrate_sqlite_to_supabase.py --dry-run
"""

import os
import sys
import json
import sqlite3
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import text, func

# Fix Windows console UTF-8 output if possible
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import komponen database dari database.py
import database
from database import Project, Chapter, StoryBible, get_session, init_db

# Load environment
load_dotenv(override=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("migration")


def parse_datetime(val):
    """Mengonversi nilai datetime SQLite string menjadi object Python datetime."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    val = str(val).strip()
    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
    )
    for fmt in formats:
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return None


def find_default_sqlite_db():
    """Mencari file database SQLite lokal secara otomatis."""
    candidates = [
        "data/story_studio.db",
        "story_studio.db",
        "writer.db",
        "database.db",
        "data/oo.db",
        "data/writer.db",
    ]
    for path in candidates:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
    
    # Cari *.db di direktori saat ini dan folder data/
    for root in [".", "data"]:
        if os.path.exists(root):
            for file in os.listdir(root):
                if file.endswith(".db") and not file.startswith("."):
                    full_path = os.path.join(root, file)
                    if os.path.getsize(full_path) > 0:
                        return full_path
    return None


def get_json_bible_path(project_name, json_dir="projects"):
    """Mengambil path file _bible.json berdasarkan nama proyek."""
    safe_name = "".join([c for c in project_name if c.isalnum() or c in (' ', '_')]).rstrip()
    return os.path.join(json_dir, f"{safe_name}_bible.json")


def get_json_rel_path(project_name, json_dir="projects"):
    """Mengambil path file _relationships.json berdasarkan nama proyek."""
    safe_name = "".join([c for c in project_name if c.isalnum() or c in (' ', '_')]).rstrip()
    return os.path.join(json_dir, f"{safe_name}_relationships.json")


def load_bible_from_json(project_name, json_dir="projects"):
    """Membaca story bible dari file JSON lokal jika ada."""
    bible_path = get_json_bible_path(project_name, json_dir)
    if os.path.exists(bible_path):
        try:
            with open(bible_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Gagal membaca file {bible_path}: {e}")
    return None


def load_relationships_from_json(project_name, json_dir="projects"):
    """Membaca relationship memory dari file JSON lokal jika ada."""
    rel_path = get_json_rel_path(project_name, json_dir)
    if os.path.exists(rel_path):
        try:
            with open(rel_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Gagal membaca file {rel_path}: {e}")
    return None


def migrate(sqlite_path: str, json_dir: str = "projects", dry_run: bool = False):
    """
    Fungsi utama untuk memigrasikan data dari SQLite ke Supabase.
    """
    if not os.path.exists(sqlite_path):
        logger.error(f"File SQLite tidak ditemukan di: {sqlite_path}")
        sys.exit(1)

    print("=" * 65)
    print("[MIGRASI] MEMULAI MIGRASI SQLITE -> SUPABASE POSTGRESQL")
    print("=" * 65)
    print(f"[*] Sumber SQLite        : {os.path.abspath(sqlite_path)}")
    print(f"[*] Folder JSON Proyek   : {os.path.abspath(json_dir)}")
    print(f"[*] Mode Dry Run         : {'YA (Simulasi tanpa menyimpan ke DB)' if dry_run else 'TIDAK (Data langsung disimpan)'}")
    
    # Hubungkan ke SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # Periksa tabel yang ada di SQLite
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    available_tables = {row["name"] for row in sqlite_cur.fetchall()}
    logger.info(f"Tabel ditemukan di SQLite: {sorted(list(available_tables))}")

    # Inisialisasi skema di Supabase
    logger.info("Memastikan tabel Supabase PostgreSQL siap...")
    try:
        init_db()
        engine = database.get_engine()
        sanitized_url = engine.url.render_as_string(hide_password=True)
        logger.info(f"Terhubung ke Supabase: {sanitized_url}")
    except Exception as e:
        logger.error(f"Gagal menghubungkan ke Supabase: {e}")
        sqlite_conn.close()
        sys.exit(1)

    # Statistik Migrasi
    stats = {
        "projects_inserted": 0,
        "projects_skipped": 0,
        "chapters_inserted": 0,
        "chapters_skipped": 0,
        "bibles_inserted": 0,
        "bibles_skipped": 0,
        "bibles_updated": 0,
    }

    # Buka sesi Supabase
    with get_session() as session:
        # ---------------------------------------------------------
        # 1. MIGRASI PROJECTS
        # ---------------------------------------------------------
        print("\n" + "-" * 40)
        print("[TAHAP 1] Migrasi Projects")
        print("-" * 40)

        # Map SQLite project ID -> Supabase project ID
        sqlite_to_supabase_pid = {}
        # Map Project Name -> Supabase project ID
        project_name_to_supabase_pid = {}

        sqlite_projects = []
        if "projects" in available_tables:
            sqlite_cur.execute("SELECT id, name, created_at FROM projects ORDER BY id ASC")
            sqlite_projects = sqlite_cur.fetchall()
            logger.info(f"Ditemukan {len(sqlite_projects)} project di SQLite.")

        # Ambil semua project yang sudah ada di Supabase
        existing_supabase_projects = {
            p.name.strip().lower(): p for p in session.query(Project).all()
        }

        for row in sqlite_projects:
            s_id = row["id"]
            name = str(row["name"]).strip()
            created_at = parse_datetime(row["created_at"])
            name_key = name.lower()

            if name_key in existing_supabase_projects:
                target_p = existing_supabase_projects[name_key]
                sqlite_to_supabase_pid[s_id] = target_p.id
                project_name_to_supabase_pid[name] = target_p.id
                stats["projects_skipped"] += 1
                print(f"  [SKIP] Project '{name}' sudah ada di Supabase (ID: {target_p.id})")
            else:
                new_project = Project(
                    name=name,
                    created_at=created_at or datetime.now()
                )
                if not dry_run:
                    session.add(new_project)
                    session.flush()  # Dapatkan ID yang baru digenerate
                    sqlite_to_supabase_pid[s_id] = new_project.id
                    project_name_to_supabase_pid[name] = new_project.id
                    existing_supabase_projects[name_key] = new_project
                else:
                    # Dummy ID untuk dry run
                    sqlite_to_supabase_pid[s_id] = 999000 + s_id
                    project_name_to_supabase_pid[name] = 999000 + s_id

                stats["projects_inserted"] += 1
                new_id = sqlite_to_supabase_pid[s_id]
                print(f"  [INSERT] Project '{name}' berhasil disalin (Supabase ID: {new_id})")

        # ---------------------------------------------------------
        # 2. MIGRASI CHAPTERS
        # ---------------------------------------------------------
        print("\n" + "-" * 40)
        print("[TAHAP 2] Migrasi Chapters")
        print("-" * 40)

        sqlite_chapters = []
        if "chapters" in available_tables:
            sqlite_cur.execute("""
                SELECT id, project_id, title, storyline, content, tone, length,
                       summary, created_at, provider, model, writing_profile
                FROM chapters
                ORDER BY id ASC
            """)
            sqlite_chapters = sqlite_cur.fetchall()
            logger.info(f"Ditemukan {len(sqlite_chapters)} chapter di SQLite.")

        for row in sqlite_chapters:
            orig_pid = row["project_id"]
            target_pid = sqlite_to_supabase_pid.get(orig_pid)

            if not target_pid:
                logger.warning(
                    f"Chapter ID {row['id']} ('{row['title']}') dilewati karena Project ID {orig_pid} tidak terdaftar."
                )
                stats["chapters_skipped"] += 1
                continue

            ch_title = (row["title"] or "").strip()
            ch_created_at = parse_datetime(row["created_at"])
            ch_content = row["content"] or ""

            # Periksa apakah chapter sudah ada di Supabase untuk project ini
            # Kriteria duplikat: project_id sama, title sama, dan (created_at sama ATAU content sama)
            query = session.query(Chapter).filter(
                Chapter.project_id == target_pid,
                Chapter.title == ch_title
            )
            candidate_chapters = query.all()

            is_duplicate = False
            for ech in candidate_chapters:
                # Cek kesamaan created_at (hingga detik) atau kesamaan isi content
                same_time = (
                    ch_created_at and ech.created_at and
                    abs((ch_created_at - ech.created_at).total_seconds()) < 2
                )
                same_content = (ch_content and ech.content and ch_content == ech.content)

                if same_time or same_content:
                    is_duplicate = True
                    break

            if is_duplicate:
                stats["chapters_skipped"] += 1
                print(f"  [SKIP] Chapter '{ch_title}' (Project ID: {target_pid}) sudah ada di Supabase.")
            else:
                new_chapter = Chapter(
                    project_id=target_pid,
                    title=ch_title,
                    storyline=row["storyline"],
                    content=ch_content,
                    tone=row["tone"],
                    length=row["length"],
                    summary=row["summary"],
                    created_at=ch_created_at or datetime.now(),
                    provider=row["provider"],
                    model=row["model"],
                    writing_profile=row["writing_profile"],
                )
                if not dry_run:
                    session.add(new_chapter)
                stats["chapters_inserted"] += 1
                print(f"  [INSERT] Chapter '{ch_title}' (Project ID: {target_pid}) disalin.")

        # ---------------------------------------------------------
        # 3. MIGRASI STORY BIBLES & RELATIONSHIPS
        # ---------------------------------------------------------
        print("\n" + "-" * 40)
        print("[TAHAP 3] Migrasi Story Bibles & Relationships")
        print("-" * 40)

        # 3a. Baca dari tabel SQLite story_bibles jika ada datanya
        sqlite_bibles_by_project = {}
        if "story_bibles" in available_tables:
            sqlite_cur.execute("SELECT * FROM story_bibles")
            for sb_row in sqlite_cur.fetchall():
                p_name = sb_row["project_name"]
                sqlite_bibles_by_project[p_name.strip().lower()] = sb_row

        # Kumpulkan semua nama project yang perlu diperiksa story bibles-nya
        all_project_names = set(project_name_to_supabase_pid.keys())
        for row in sqlite_projects:
            all_project_names.add(str(row["name"]).strip())

        # Ambil story bibles yang sudah ada di Supabase
        existing_supabase_bibles = {
            b.project_name.strip().lower(): b for b in session.query(StoryBible).all()
        }

        for proj_name in sorted(list(all_project_names)):
            proj_name_key = proj_name.lower()
            supabase_bible = existing_supabase_bibles.get(proj_name_key)

            # Cek sumber data Story Bible:
            # 1. Dari SQLite story_bibles tabel
            characters = ""
            relationships = ""
            setting = ""
            context = ""
            writing_rules = ""
            relationship_memory = "{}"

            data_source = None

            if proj_name_key in sqlite_bibles_by_project:
                sb = sqlite_bibles_by_project[proj_name_key]
                characters = sb["characters"] or ""
                relationships = sb["relationships"] or ""
                setting = sb["setting"] or ""
                context = sb["context"] or ""
                writing_rules = sb["writing_rules"] or ""
                relationship_memory = sb["relationship_memory"] or "{}"
                data_source = "SQLite Table"

            # 2. Jika SQLite kosong atau tidak lengkap, fallback ke file JSON di projects/
            json_bible = load_bible_from_json(proj_name, json_dir)
            json_rel = load_relationships_from_json(proj_name, json_dir)

            if json_bible:
                characters = characters or json_bible.get("characters", "")
                relationships = relationships or json_bible.get("relationships", "")
                setting = setting or json_bible.get("setting", "")
                context = context or json_bible.get("context", "")
                writing_rules = writing_rules or json_bible.get("writing_rules", "")
                if not data_source:
                    data_source = "JSON Files"
                else:
                    data_source += " + JSON Fallback"

            if json_rel:
                try:
                    relationship_memory = json.dumps(json_rel, indent=4)
                    if not data_source:
                        data_source = "JSON Relationships"
                except Exception:
                    pass

            # Lewati jika tidak ada data sama sekali untuk project ini
            has_data = any([characters, relationships, setting, context, writing_rules]) or (relationship_memory and relationship_memory != "{}")
            if not has_data:
                continue

            if supabase_bible:
                # Periksa apakah Supabase story bible kosong dan bisa di-update
                is_empty = not any([
                    supabase_bible.characters,
                    supabase_bible.relationships,
                    supabase_bible.setting,
                    supabase_bible.context,
                    supabase_bible.writing_rules,
                ]) and (not supabase_bible.relationship_memory or supabase_bible.relationship_memory in ("{}", ""))

                if is_empty:
                    if not dry_run:
                        supabase_bible.characters = characters
                        supabase_bible.relationships = relationships
                        supabase_bible.setting = setting
                        supabase_bible.context = context
                        supabase_bible.writing_rules = writing_rules
                        supabase_bible.relationship_memory = relationship_memory
                    stats["bibles_updated"] += 1
                    print(f"  [UPDATE] Story Bible untuk '{proj_name}' diperbarui dari {data_source}.")
                else:
                    stats["bibles_skipped"] += 1
                    print(f"  [SKIP] Story Bible untuk '{proj_name}' sudah ada & terisi di Supabase.")
            else:
                new_bible = StoryBible(
                    project_name=proj_name,
                    characters=characters,
                    relationships=relationships,
                    setting=setting,
                    context=context,
                    writing_rules=writing_rules,
                    relationship_memory=relationship_memory,
                    updated_at=datetime.now()
                )
                if not dry_run:
                    session.add(new_bible)
                stats["bibles_inserted"] += 1
                print(f"  [INSERT] Story Bible untuk '{proj_name}' disalin (Sumber: {data_source}).")

        # ---------------------------------------------------------
        # 4. SINKRONISASI SEQUENCE POSTGRESQL
        # ---------------------------------------------------------
        if not dry_run:
            print("\n" + "-" * 40)
            print("[TAHAP 4] Sinkronisasi Sequence ID Supabase")
            print("-" * 40)
            session.flush()

            tables_to_sync = ["projects", "chapters", "story_bibles"]
            for tbl in tables_to_sync:
                try:
                    # Sinkronkan sequence serial Postgres agar ID baru tidak konflik
                    sync_query = text(f"""
                        SELECT setval(
                            pg_get_serial_sequence('{tbl}', 'id'),
                            COALESCE((SELECT MAX(id) FROM {tbl}), 1)
                        );
                    """)
                    session.execute(sync_query)
                    print(f"  [SYNC] Sequence ID untuk tabel '{tbl}' berhasil disinkronkan.")
                except Exception as seq_err:
                    logger.debug(f"Pemberitahuan sinkronisasi sequence untuk {tbl}: {seq_err}")

        # Jika dry-run, rollback agar tidak mengubah apapun
        if dry_run:
            session.rollback()
            print("\n[PERINGATAN] Mode Dry Run aktif: Tidak ada perubahan yang disimpan ke Supabase.")

    sqlite_conn.close()

    # ---------------------------------------------------------
    # RINGKASAN HASIL MIGRASI
    # ---------------------------------------------------------
    print("\n" + "=" * 65)
    print("[HASIL] RINGKASAN MIGRASI")
    print("=" * 65)
    print(f"  * Projects    : {stats['projects_inserted']} disalin, {stats['projects_skipped']} dilewati (sudah ada)")
    print(f"  * Chapters    : {stats['chapters_inserted']} disalin, {stats['chapters_skipped']} dilewati (duplikat/sudah ada)")
    print(f"  * Story Bibles: {stats['bibles_inserted']} disalin, {stats['bibles_updated']} diupdate, {stats['bibles_skipped']} dilewati")
    print("=" * 65)
    if dry_run:
        print("[INFO] Ini hanya simulasi. Jalankan tanpa flag --dry-run untuk mengeksekusi.")
    else:
        print("[SUKSES] Migrasi selesai dengan sukses!")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Migrasikan data SQLite lokal ke Supabase PostgreSQL (Projects, Chapters, Story Bibles)."
    )
    parser.add_argument(
        "--sqlite", "-s",
        type=str,
        default=None,
        help="Path ke file database SQLite lokal (contoh: data/story_studio.db atau writer.db). Jika tidak ditentukan, skrip akan mendeteksi otomatis."
    )
    parser.add_argument(
        "--json-dir", "-j",
        type=str,
        default="projects",
        help="Direktori tempat file JSON project story bible berada (default: projects)."
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Simulasikan migrasi tanpa menyimpan perubahan ke database Supabase."
    )

    args = parser.parse_args()

    # Tentukan path SQLite
    sqlite_path = args.sqlite
    if not sqlite_path:
        sqlite_path = find_default_sqlite_db()
        if not sqlite_path:
            logger.error(
                "Tidak ditemukan file database SQLite otomatis (misal: data/story_studio.db, writer.db, database.db).\n"
                "Silakan tentukan path secara manual menggunakan argumen --sqlite, contoh:\n"
                "    python migrate_sqlite_to_supabase.py --sqlite data/story_studio.db"
            )
            sys.exit(1)
        logger.info(f"File SQLite terdeteksi otomatis: {sqlite_path}")

    migrate(sqlite_path=sqlite_path, json_dir=args.json_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
