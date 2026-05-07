import sqlite3
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename='system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_NAME = "pipeline.db"

def init_db():
    """Initializes the SQLite database and creates the necessary table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal_ekstrak TEXT NOT NULL,
                data_json TEXT NOT NULL,
                status TEXT NOT NULL
            )
        ''')
        conn.commit()
        logging.info("Tabel 'api_data' siap atau sudah ada dengan mode WAL.")
    except sqlite3.Error as e:
        logging.error(f"Gagal inisialisasi database SQLite. Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def insert_data(data: Dict[str, Any], status: str = "success") -> bool:
    """
    Inserts JSON data into the database.

    Args:
        data (Dict[str, Any]): The parsed JSON dictionary from the CLI parser.
        status (str): The status of the extraction process.

    Returns:
        bool: True if insert was successful, False otherwise.
    """
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        cursor = conn.cursor()

        tanggal_ekstrak = datetime.now().isoformat()
        data_json_str = json.dumps(data)

        cursor.execute(
            "INSERT INTO api_data (tanggal_ekstrak, data_json, status) VALUES (?, ?, ?)",
            (tanggal_ekstrak, data_json_str, status)
        )

        conn.commit()
        logging.info("Berhasil menyimpan data JSON ke database.")
        return True
    except sqlite3.Error as e:
        logging.error(f"Gagal melakukan insert data ke database. Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def get_latest_data() -> Optional[Dict[str, Any]]:
    """
    Retrieves the most recent successful data from the database.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the record, or None if not found/error.
    """
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        # return rows as dicts
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM api_data WHERE status = 'success' ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()

        if row:
            logging.info("Berhasil mengambil data terbaru dari database.")
            # Construct a response dictionary
            return {
                "id": row["id"],
                "tanggal_ekstrak": row["tanggal_ekstrak"],
                "data": json.loads(row["data_json"]),
                "status": row["status"]
            }
        else:
            logging.info("Tidak ada data 'success' ditemukan di database.")
            return None

    except sqlite3.Error as e:
        logging.error(f"Gagal mengambil data dari database. Error: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Data JSON rusak di database untuk id={row['id']} jika ada. Error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def get_historical_data(limit: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieves the most recent successful records from the database.

    Args:
        limit (int): The maximum number of records to retrieve.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of dictionaries containing the records, or None if error.
    """
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM api_data WHERE status = 'success' ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()

        if rows:
            logging.info(f"Berhasil mengambil {len(rows)} data historis dari database.")
            results = []
            for row in rows:
                try:
                    results.append({
                        "id": row["id"],
                        "tanggal_ekstrak": row["tanggal_ekstrak"],
                        "data": json.loads(row["data_json"]),
                        "status": row["status"]
                    })
                except json.JSONDecodeError as e:
                    logging.error(f"Data JSON rusak di database untuk id={row['id']} jika ada. Error: {e}")
                    continue
            return results
        else:
            logging.info("Tidak ada data 'success' ditemukan di database untuk historis.")
            return []

    except sqlite3.Error as e:
        logging.error(f"Gagal mengambil data historis dari database. Error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_db()
