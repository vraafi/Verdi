import subprocess
import logging
import json
import re
import os
import random
import tempfile
from typing import Optional, Dict, Any

# Ensure logger config matches system
logging.basicConfig(
    filename='system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def process_with_llm_cli(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Processes raw text using a local CLI tool (gemini-cli) via subprocess.

    Args:
        raw_text (str): The raw text extracted by the scraper.

    Returns:
        Optional[Dict[str, Any]]: A parsed JSON dictionary, or None if it fails.
    """
    if not raw_text:
        logging.error("Teks input kosong. Menghentikan pemrosesan AI.")
        return None

    # Truncate text to avoid context window overflow for smaller models
    max_chars = 15000
    if len(raw_text) > max_chars:
        logging.info(f"Teks mentah terlalu panjang ({len(raw_text)} chars). Memotong menjadi {max_chars} chars.")
        raw_text = raw_text[:max_chars]

    prompt = (
        "Berikut adalah gabungan teks mentah dari Hacker News, GitHub Trending, dan Dev.to. "
        "Analisis data ini dan ekstrak menjadi format JSON. "
        "Wajib mengikuti struktur schema ini secara ketat:\n"
        "{\n"
        '  "top_5_tech_topics": ["Tech1", "Tech2", "Tech3", "Tech4", "Tech5"],\n'
        '  "overall_sentiment": "Positif/Negatif/Netral",\n'
        '  "summary": "Satu paragraf singkat 50 kata mengenai trend saat ini."\n'
        "}\n\n"
        "CONTOH INPUT:\n"
        "--- SUMBER: https://github.com/trending ---\n"
        "Rust is a blazing fast language. Python is great for AI.\n"
        "CONTOH OUTPUT JSON:\n"
        "{\n"
        '  "top_5_tech_topics": ["Rust", "Python", "AI", "Performance", "Programming"],\n'
        '  "overall_sentiment": "Positif",\n'
        '  "summary": "Rust and Python are currently trending, particularly for their performance and AI capabilities."\n'
        "}\n\n"
        "KEMBALIKAN HANYA JSON VALID TANPA MARKDOWN. JANGAN TAMBAHKAN TEKS LAIN."
    )

    # Menyiapkan perintah CLI
    combined_input = f"{prompt}\n\nTeks:\n{raw_text}"

    # Fallback Chain Models
    models = [
        "models/gemma-4-31b-it",
        "models/gemma-4-26b-a4b-it",
        "models/gemma-3-27b-it",
        "models/gemini-3.1-flash-lite-preview",
        "models/gemma-3-12b-it",
        "models/gemma-3-4b-it",
        "models/gemma-3n-e4b-it",
        "models/gemma-3n-e2b-it",
        "models/gemma-3-1b-it"
    ]

    # Ambil list API Keys untuk dirotasi jika ada
    api_keys_str = os.getenv("GEMINI_API_KEYS", "")
    api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]

    for model in models:
        # Flag -y agar tidak interaktif
        command = ["gemini-cli", "--model", model, "-y"]

        # Buat temporary directory untuk HOME unik per session
        with tempfile.TemporaryDirectory() as temp_home_dir:
            env_vars = os.environ.copy()
            env_vars["HOME"] = temp_home_dir
            env_vars["CI"] = "true"  # Supaya gemini-cli tahu ini mode otomatis

            # Rotasi kunci jika ada
            if api_keys:
                selected_key = random.choice(api_keys)
                env_vars["GEMINI_API_KEY"] = selected_key

            try:
                logging.info(f"Mulai memanggil gemini-cli subprocess menggunakan model: {model} dengan temp HOME")
                result = subprocess.run(
                    command,
                    input=combined_input,
                    capture_output=True,
                    text=True,
                    env=env_vars,
                    timeout=30 # 30 detik timeout batas eksekusi
                )

                if result.returncode != 0:
                    logging.error(f"Eksekusi gemini-cli gagal dengan model {model} (return code {result.returncode}). Stderr: {result.stderr.strip()}")
                    continue # Lanjut ke model berikutnya

                raw_output = result.stdout.strip()

                # Bersihkan format markdown jika model me-return ```json ... ```
                clean_json_str = raw_output
                if clean_json_str.startswith("```"):
                    # Gunakan regex untuk mengambil teks di dalam blok ```json ... ``` atau sekedar ``` ... ```
                    match = re.search(r'```(?:json)?(.*?)```', raw_output, re.DOTALL)
                    if match:
                        clean_json_str = match.group(1).strip()
                    else:
                        # Jika regex tidak match tapi ada ``` di awal, kita potong manual (edge case)
                        clean_json_str = clean_json_str.replace("```json", "").replace("```", "").strip()

                # Parse JSON
                parsed_json = json.loads(clean_json_str)

                # Validasi Schema
                if not isinstance(parsed_json, dict):
                    raise ValueError("Output JSON bukan dictionary")
                if "top_5_tech_topics" not in parsed_json or not isinstance(parsed_json["top_5_tech_topics"], list):
                    raise ValueError("Schema error: 'top_5_tech_topics' hilang atau bukan list")
                if "overall_sentiment" not in parsed_json or not isinstance(parsed_json["overall_sentiment"], str):
                    raise ValueError("Schema error: 'overall_sentiment' hilang atau bukan string")
                if "summary" not in parsed_json or not isinstance(parsed_json["summary"], str):
                    raise ValueError("Schema error: 'summary' hilang atau bukan string")

                logging.info(f"Berhasil parsing dan validasi schema output JSON dengan model: {model}")
                return parsed_json

            except subprocess.TimeoutExpired:
                logging.error(f"Proses gemini-cli timeout dengan model {model}.")
                continue
            except FileNotFoundError:
                logging.error("Executable 'gemini-cli' tidak ditemukan di sistem (PATH).")
                return None # Fail fast if binary missing
            except json.JSONDecodeError as e:
                logging.error(f"Gagal mem-parsing output JSON dengan model {model}. Error: {e}")
                continue
            except Exception as e:
                logging.error(f"Kesalahan tak terduga dengan model {model}. Error: {e}")
                continue

    logging.error("Semua model dalam fallback chain gagal diproses.")
    return None
