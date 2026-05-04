from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
import logging
import os

from database import init_db, get_latest_data

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

# Server akan dijalankan menggunakan Uvicorn di command line
# Contoh: RAPIDAPI_SECRET="my_secret" uvicorn main:app --host 0.0.0.0 --port 8000
