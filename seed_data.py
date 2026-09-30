# import os
# import sqlite3
# import json
# from database import DB_PATH, init_db, create_project, save_chapter
# from bible_manager import save_bible
# from relationship_manager import save_relationships

# def seed():
#     print("Starting database seeding...")

#     # 1. Reset Database
#     if os.path.exists(DB_PATH):
#         os.remove(DB_PATH)
#         print(f"Removed existing database at {DB_PATH}")
    
#     init_db()
#     print("Database initialized.")

#     # 2. Define Project Data
#     project_name = "Aegis Terakhir"
#     project_id = create_project(project_name)
    
#     if project_id is None:
#         print(f"Failed to create project '{project_name}'. It might already exist.")
#         return

#     print(f"Project '{project_name}' created with ID: {project_id}")

#     # 3. Define Bible Data
#     bible_data = {
#         "characters": (
#             "- Komandan Elara Vance: Pemimpin ekspedisi yang tegas. Berusia 42 tahun, mantan pilot tempur. Memiliki bekas luka di pelipis kiri.\n"
#             "- Kaelen: AI pusat kapal Aegis. Memiliki kepribadian yang tenang namun sarkastik.\n"
#             "- Dr. Aris Thorne: Kepala ilmuwan dan medis. Pria paruh baya yang selalu optimis, ahli dalam xenobiologi."
#         ),
#         "relationships": (
#             "- Elara dan Kaelen: Hubungan simbiosis antara manusia dan mesin. Elara sering berbicara dengan Kaelen saat ia merasa kesepian.\n"
#             "- Elara dan Aris: Teman dekat sejak di Akademi. Ada ketegangan romantis yang dipendam selama bertahun-tahun."
#         ),
#         "setting": (
#             "Starship Aegis, kapal koloni terakhir umat manusia yang melarikan diri dari kehancuran Tata Surya. "
#             "Saat ini berada di tepian Nebula Orion, dikelilingi oleh awan gas berwarna ungu dan debu bintang."
#         ),
#         "writing_rules": (
#             "- Gunakan sudut pandang orang ketiga terbatas (Elara).\n"
#             "- Fokus pada detail teknis fiksi ilmiah dan suasana yang sunyi di ruang angkasa.\n"
#             "- Dialog harus terasa natural namun profesional."
#         ),
#         "context": "Kapal baru saja keluar dari warp dan menemukan sesuatu yang tidak seharusnya ada di sana."
#     }
#     save_bible(project_name, bible_data)
#     print("Story Bible saved.")

#     # 4. Define Relationship Memory
#     relationship_data = {
#         "running_gags": {"content": "Kaelen selalu mengingatkan Elara untuk minum kopi, meskipun Kaelen tahu kopi di kapal sudah habis.", "priority": "Low"},
#         "habits": {"content": "Elara selalu mengetukkan jarinya ke konsol saat sedang berpikir keras.", "priority": "Medium"},
#         "love_languages": {"content": "Aris sering membawakan ransum tambahan untuk Elara sebagai bentuk perhatian.", "priority": "High"},
#         "comfort_behaviors": {"content": "Saat stres, Elara akan pergi ke dek observasi untuk melihat bintang.", "priority": "Medium"},
#         "inside_jokes": {"content": "Sebutan 'Sirkus Terbang' untuk kegagalan latihan pertama mereka di Mars.", "priority": "Low"},
#         "daily_rituals": {"content": "Briefing pagi di jembatan kapten setiap pukul 08:00 waktu kapal.", "priority": "Medium"},
#         "nicknames": {"content": "Kaelen memanggil Elara 'Kapten' dengan nada sedikit mengejek saat bercanda.", "priority": "Low"},
#         "pet_peeves": {"content": "Elara benci jika Aris meninggalkan peralatan medisnya berantakan.", "priority": "Medium"},
#         "shared_memories": {"content": "Momen saat mereka melihat Bumi menghilang di cakrawala untuk terakhir kalinya.", "priority": "High"},
#         "relationship_evolution": {"content": "Kepercayaan antara Elara dan Aris semakin menguat setelah insiden kebocoran oksigen di sektor 4.", "priority": "High"}
#     }
#     save_relationships(project_name, relationship_data)
#     print("Relationship memory saved.")

#     # 5. Define Chapters
#     chapters = [
#         {
#             "title": "Bab 1: Kebangunan yang Dingin",
#             "storyline": "Elara terbangun dari stasis lebih awal karena alarm malfungsi. Kapal terasa sangat sepi.",
#             "content": (
#                 "Desisan udara dingin menyambut Elara saat kapsul stasisnya terbuka. Cairan kriogenik menetes dari tubuhnya, "
#                 "menciptakan genangan kecil di lantai logam yang beku. Matanya mencoba fokus pada cahaya merah yang berkedip-kedip di langit-langit.\n\n"
#                 "'Selamat pagi, Kapten,' suara Kaelen bergema di ruangan yang sunyi itu. Ada nada datar yang tidak biasanya.\n\n"
#                 "'Kaelen? Kenapa aku dibangunkan? Kita masih lima tahun dari tujuan,' bisik Elara, suaranya serak karena tidur panjang.\n\n"
#                 "'Ada anomali, Kapten. Sesuatu yang cukup besar untuk menarik kita keluar dari ruang warp. Dan saya rasa Anda harus melihat ini.'"
#             ),
#             "tone": "Tegang dan Atmosferik",
#             "length": "Sekitar 500 kata",
#             "summary": "Elara terbangun prematur dari stasis oleh Kaelen karena anomali misterius yang menarik kapal keluar dari jalur warp.",
#             "provider": "gemini",
#             "model": "gemini-1.5-pro",
#             "writing_profile": "standard"
#         },
#         {
#             "title": "Bab 2: Gema di Kegelapan",
#             "storyline": "Elara dan Aris memeriksa jembatan kapal dan menemukan objek raksasa di radar.",
#             "content": (
#                 "Layar utama jembatan kapal Aegis menampilkan kegelapan absolut, sampai sebuah kontur raksasa mulai terlihat. "
#                 "Itu bukan asteroid. Strukturnya terlalu simetris, terlalu... buatan. Dr. Aris Thorne berdiri di samping Elara, "
#                 "wajahnya yang biasanya optimis kini terlihat pucat pasi.\n\n"
#                 "'Elara, itu bukan teknologi kita,' kata Aris pelan. Tangannya gemetar saat ia menyentuh layar radar. "
#                 "'Lihat fluktuasi energinya. Itu murni tenaga gravitasi.'\n\n"
#                 "Elara menatap objek itu—sebuah cakram raksasa yang tampak menelan cahaya di sekitarnya. "
#                 "'Kaelen, bisa kau identifikasi asalnya?'\n\n"
#                 "'Tidak ada dalam database sejarah manusia, Kapten. Tapi sinyalnya... itu adalah kode biner kuno. Kode yang kita gunakan seribu tahun lalu.'"
#             ),
#             "tone": "Penuh Misteri",
#             "length": "Sekitar 600 kata",
#             "summary": "Elara dan Aris menemukan objek buatan raksasa yang memancarkan sinyal biner kuno, menunjukkan adanya hubungan dengan masa lalu manusia yang hilang.",
#             "provider": "gemini",
#             "model": "gemini-1.5-pro",
#             "writing_profile": "standard"
#         }
#     ]

#     for ch in chapters:
#         save_chapter(
#             project_id=project_id,
#             title=ch["title"],
#             storyline=ch["storyline"],
#             content=ch["content"],
#             tone=ch["tone"],
#             length=ch["length"],
#             summary=ch["summary"],
#             provider=ch["provider"],
#             model=ch["model"],
#             writing_profile=ch["writing_profile"]
#         )
#         print(f"Chapter '{ch['title']}' saved.")

#     print("\nSeeding completed successfully!")
#     print(f"Database: {DB_PATH}")
#     print(f"Project JSONs created in the 'projects' directory.")

# if __name__ == "__main__":
#     seed()
