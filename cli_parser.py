import subprocess
import logging
import json
import re
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
        "Ekstrak entitas penting dari teks berikut (Judul, Harga/Data Utama, Sentimen/Ringkasan). "
        "Kembalikan HANYA format JSON valid."
    )

    # Menyiapkan perintah CLI
    # Kita asumsikan gemini-cli menerima argumen berupa teks gabungan antara prompt dan raw text,
    # atau mungkin menerima prompt sebagai satu argumen dan input text sebagai stdin/argumen lain.
    # Karena instruksi menyebut "Masukkan prompt dan teks kotor tersebut sebagai argumen atau input",
    # kita gabungkan dalam satu argumen string untuk dieksekusi.
    combined_input = f"{prompt}\n\nTeks:\n{raw_text}"

    command = ["gemini-cli", combined_input]

    try:
        logging.info("Mulai memanggil gemini-cli subprocess...")
        # Menjalankan subprocess, timeout mencegah VPS macet jika hang
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30 # 30 detik timeout batas eksekusi
        )

        if result.returncode != 0:
            logging.error(f"Eksekusi gemini-cli gagal dengan return code {result.returncode}. Stderr: {result.stderr.strip()}")
            return None

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
        logging.info("Berhasil parsing output gemini-cli menjadi JSON.")
        return parsed_json

    except subprocess.TimeoutExpired:
        logging.error("Proses gemini-cli timeout setelah 30 detik.")
        return None
    except FileNotFoundError:
        logging.error("Executable 'gemini-cli' tidak ditemukan di sistem (PATH).")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Gagal mem-parsing output JSON. Error: {e}. Raw Output: {raw_output}")
        return None
    except Exception as e:
        logging.error(f"Kesalahan tak terduga saat memanggil gemini-cli. Error: {e}")
        return None
