from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import os

from database import init_db, get_latest_data, insert_data, get_historical_data, get_data_by_id
from scraper import scrape_data
from cli_parser import process_with_llm_cli

# Inisialisasi DB saat mulai
init_db()

# Setup logging
logging.basicConfig(
    filename='system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Data API Pipeline",
    description="API untuk menyajikan data yang diekstrak dan diproses oleh LLM CLI",
    version="1.0.1"
)

def verify_rapidapi_secret(x_rapidapi_proxy_secret: str = Header(None)):
    """
    Dependency check for X-RapidAPI-Proxy-Secret header.
    """
    expected_secret = os.getenv('RAPIDAPI_SECRET')

    # Optional: Log attempt (do not log the actual secret for security)
    if not x_rapidapi_proxy_secret:
        logging.error("Akses ditolak: Header X-RapidAPI-Proxy-Secret hilang.")
        raise HTTPException(status_code=403, detail="Forbidden: Missing RapidAPI Proxy Secret header")

    if x_rapidapi_proxy_secret != expected_secret:
        logging.error("Akses ditolak: Header X-RapidAPI-Proxy-Secret tidak valid.")
        raise HTTPException(status_code=403, detail="Forbidden: Invalid RapidAPI Proxy Secret")

    return True

@app.get("/health", response_class=JSONResponse)
def health_check():
    """
    Open endpoint for monitoring.
    """
    return {"status": "ok", "message": "Service is running."}

@app.get("/api/v1/data/latest", response_class=JSONResponse, dependencies=[Depends(verify_rapidapi_secret)])
def get_latest_pipeline_data():
    """
    Endpoint untuk mengambil data terbaru yang berhasil diproses dari SQLite.
    Returns:
        JSON murni.
    """
    logging.info("Menerima request terverifikasi untuk endpoint GET /api/v1/data/latest")

    data_record = get_latest_data()

    if data_record is None:
        logging.error("Data tidak ditemukan atau terjadi error saat mengambil data")
        raise HTTPException(status_code=404, detail="No data available")

    return data_record

@app.get("/api/v1/data/history", response_class=JSONResponse, dependencies=[Depends(verify_rapidapi_secret)])
def get_pipeline_data_history(limit: int = 10, offset: int = 0):
    """
    Endpoint untuk mengambil historis data yang berhasil diproses dari SQLite dengan paginasi.
    Returns:
        JSON array murni.
    """
    # Strict limits for API endpoints to prevent DB DoS
    if limit > 50:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 50")
    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be at least 1")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset cannot be negative")

    logging.info(f"Menerima request terverifikasi GET /api/v1/data/history (limit={limit}, offset={offset})")

    data_records = get_historical_data(limit=limit, offset=offset)

    if data_records is None:
        logging.error("Terjadi error saat mengambil data historis")
        raise HTTPException(status_code=500, detail="Internal server error while fetching history")

    return {"count": len(data_records), "offset": offset, "limit": limit, "data": data_records}

@app.get("/api/v1/data/{record_id}", response_class=JSONResponse, dependencies=[Depends(verify_rapidapi_secret)])
def get_pipeline_data_by_id(record_id: int):
    """
    Endpoint untuk mengambil spesifik data yang berhasil diproses berdasarkan ID.
    Returns:
        JSON murni.
    """
    logging.info(f"Menerima request terverifikasi GET /api/v1/data/{record_id}")

    data_record = get_data_by_id(record_id)

    if data_record is None:
        logging.error(f"Data dengan id={record_id} tidak ditemukan.")
        raise HTTPException(status_code=404, detail=f"No data available for id {record_id}")

    return data_record


def run_pipeline_task():
    """
    Background task to execute the data pipeline.
    """
    logging.info("Memulai background task: pipeline manual.")

    # 1. Scrape
    raw_text = scrape_data()
    if not raw_text:
        logging.error("Pipeline background gagal: Scraper tidak menghasilkan data.")
        return

    # 2. Parse AI
    parsed_json = process_with_llm_cli(raw_text)
    if not parsed_json:
        logging.error("Pipeline background gagal: AI Parser gagal memproses teks.")
        return

    # 3. Simpan ke database
    success = insert_data(parsed_json, status="success")
    if not success:
        logging.error("Pipeline background gagal: Gagal menyimpan data ke database.")
        return

    logging.info("Pipeline background berhasil dijalankan dan data telah disimpan.")


@app.post("/api/v1/pipeline/run", response_class=JSONResponse, status_code=202, dependencies=[Depends(verify_rapidapi_secret)])
def run_pipeline(background_tasks: BackgroundTasks):
    """
    Endpoint untuk menjalankan scraper, memprosesnya dengan AI CLI, dan menyimpannya ke database secara manual.
    """
    logging.info("Menerima request untuk menjalankan pipeline manual (/api/v1/pipeline/run)")

    background_tasks.add_task(run_pipeline_task)
    return {"status": "processing", "message": "Pipeline started in the background"}

# Server akan dijalankan menggunakan Uvicorn di command line
# Contoh: RAPIDAPI_SECRET="my_secret" uvicorn main:app --host 0.0.0.0 --port 8000
