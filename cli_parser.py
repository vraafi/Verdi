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

    prompt = (
        "Berikut adalah gabungan teks mentah dari Hacker News, GitHub Trending, dan Dev.to. "
        "Analisis data ini dan ekstrak menjadi format JSON dengan struktur: "
        "1. top_5_tech_topics (5 teknologi/bahasa/framework yang paling banyak dibahas), "
        "2. overall_sentiment (Positif/Negatif/Netral terhadap industri tech), dan "
        "3. summary (1 paragraf singkat 50 kata). "
        "KEMBALIKAN HANYA JSON VALID TANPA MARKDOWN."
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
                logging.info(f"Berhasil parsing output gemini-cli menjadi JSON dengan model: {model}")
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
