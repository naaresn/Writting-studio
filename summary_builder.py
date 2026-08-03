class SummaryBuilder:
    """Constructs structured prompts to generate concise summaries of chapters in Indonesian."""

    def build_summary_prompt(self, chapter_content: str) -> str:
        """
        Builds a prompt asking the AI model to summarize a chapter in Indonesian,
        focusing only on established events, character interactions, etc.
        """
        prompt = f"""
Anda adalah asisten penulis novel profesional. Buatlah ringkasan dari bab cerita berikut untuk digunakan sebagai konteks latar belakang bab selanjutnya.

ATURAN RINGKASAN:
1. Tulis ringkasan sepenuhnya dalam Bahasa Indonesia dalam bentuk paragraf naratif yang mengalir (bukan poin-poin).
2. Berikan ringkasannya saja. TIDAK PERLU menyertakan kalimat pembuka seperti "Berikut adalah ringkasan bab ini..." atau sejenisnya.
3. DILARANG menggunakan judul (heading), daftar bernomor, label, atau format Markdown apa pun dalam ringkasan.
4. Pastikan ringkasan panjangnya sekitar 120-200 kata.
5. Hanya ringkas peristiwa penting, interaksi karakter, perkembangan hubungan, fakta baru, dan keadaan akhir bab.
6. Abaikan detail visual yang tidak relevan dengan kelanjutan cerita.
7. DILARANG menambahkan interpretasi, asumsi, atau informasi yang tidak ada di teks asli.

--- ISI BAB CERITA ---
{chapter_content}

--- TUGAS ---
Buatlah ringkasan bab di atas sesuai dengan aturan di atas.
"""
        return prompt.strip()
