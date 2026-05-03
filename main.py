from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging

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
    version="1.0.0"
)

@app.get("/api/v1/data/latest", response_class=JSONResponse)
def get_latest_pipeline_data():
    """
    Endpoint untuk mengambil data terbaru yang berhasil diproses dari SQLite.
    Returns:
        JSON murni.
    """
    logging.info("Menerima request untuk endpoint GET /api/v1/data/latest")

    data_record = get_latest_data()

    if data_record is None:
        logging.error("Data tidak ditemukan atau terjadi error saat mengambil data")
        raise HTTPException(status_code=404, detail="No data available")

    return data_record

# Server akan dijalankan menggunakan Uvicorn di command line
# Contoh: uvicorn main:app --host 0.0.0.0 --port 8000
