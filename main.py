from fastapi import FastAPI, HTTPException, Depends, Header
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


@app.post("/api/v1/pipeline/run", response_class=JSONResponse, dependencies=[Depends(verify_rapidapi_secret)])
def run_pipeline():
    """
    Endpoint untuk menjalankan scraper, memprosesnya dengan AI CLI, dan menyimpannya ke database secara manual.
    """
    logging.info("Menerima request untuk menjalankan pipeline manual (/api/v1/pipeline/run)")

    # 1. Scrape
    raw_text = scrape_data()
    if not raw_text:
        logging.error("Pipeline gagal: Scraper tidak menghasilkan data.")
        raise HTTPException(status_code=500, detail="Scraping failed")

    # 2. Parse AI
    parsed_json = process_with_llm_cli(raw_text)
    if not parsed_json:
        logging.error("Pipeline gagal: AI Parser gagal memproses teks.")
        raise HTTPException(status_code=500, detail="AI Parsing failed")

    # 3. Simpan ke database
    success = insert_data(parsed_json, status="success")
    if not success:
        logging.error("Pipeline gagal: Gagal menyimpan data ke database.")
        raise HTTPException(status_code=500, detail="Database insertion failed")

    logging.info("Pipeline manual berhasil dijalankan dan data telah disimpan.")
    return {"status": "success", "message": "Pipeline run successfully and data saved"}

# Server akan dijalankan menggunakan Uvicorn di command line
# Contoh: RAPIDAPI_SECRET="my_secret" uvicorn main:app --host 0.0.0.0 --port 8000
