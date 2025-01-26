from pathlib import Path
from litestar import Litestar, get, post
from litestar.response import Template
from litestar.template import TemplateConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Stream
from litestar.datastructures import UploadFile
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST
from minio_utils import ensure_bucket_exists, upload_to_minio, delete_from_minio, minio_client, MINIO_BUCKET_NAME

from starlette.requests import Request
from litestar.exceptions import ValidationException


import subprocess
import threading
import queue
import logging
import asyncio
import os

# Create a queue to store logs
log_queue = queue.Queue()

# Configure logging to add logs to the queue
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        self.formatter = logging.Formatter('%(message)s')

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)

# Ensure the MinIO bucket exists
ensure_bucket_exists()

# Route for the homepage
@get("/")
async def home() -> Template:
    return Template("index.html")

# Route to start the web scraper
@post("/start-scraper")
async def start_scraper() -> dict:
    # Create a queue for logs if it doesn't exist
    if 'log_queue' not in globals():
        global log_queue
        log_queue = queue.Queue()

    def run_scraper():
        # Configure logging to use the queue handler
        queue_handler = QueueHandler(log_queue)
        logger = logging.getLogger()  # Root logger
        logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to prevent duplicate logging
        logger.handlers.clear()
        
        # Add the queue handler
        logger.addHandler(queue_handler)
        
        # Import and run the scraper
        import webscraper
        webscraper.scrape_tcga_data()

    # Run the scraper in a separate thread
    thread = threading.Thread(target=run_scraper)
    thread.start()

    return {"message": "Web scraper started!"}

# SSE endpoint to stream logs
@get("/logs")
async def sse_logs() -> Stream:
    async def generate_logs():
        while True:
            if not log_queue.empty():
                log = log_queue.get()
                yield f"data: {log}\n\n"
            else:
                await asyncio.sleep(1)

    return Stream(
        content=generate_logs(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

# Route to upload a file to MinIO
@post("/upload-file")
async def upload_file(request: Request) -> dict:
    try:
        form_data = await request.form()
        file = form_data["file"]  # Match the FormData key "file"

        # Validate file type
        if not file.filename.endswith(".tsv"):
            raise ValidationException("Only .tsv files are allowed.")

        # Save and upload the file
        os.makedirs("uploads", exist_ok=True)
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        if upload_to_minio(file_path, file.filename):
            os.remove(file_path)
            return {"message": f"File {file.filename} uploaded successfully!"}
        else:
            return {"message": "Upload failed"}, HTTP_400_BAD_REQUEST

    except ValidationException as e:
        return {"message": str(e)}, HTTP_400_BAD_REQUEST
    except Exception as e:
        return {"message": f"Error: {str(e)}"}, HTTP_400_BAD_REQUEST

# Route to delete a file from MinIO
@post("/delete-file")
async def delete_file(data: dict) -> dict:
    try:
        file_name = data.get("file_name")
        if not file_name:
            return {"message": "File name is required"}, HTTP_400_BAD_REQUEST

        # Delete the file from MinIO
        if delete_from_minio(file_name):
            print(f"Deleted {file_name} from MinIO")
            return {"message": f"File {file_name} deleted successfully!"}
        else:
            return {"message": f"Failed to delete {file_name} from MinIO"}, HTTP_400_BAD_REQUEST
    
    except Exception as e:
        logger.error(f"Failed to delete file: {str(e)}")
        return {"message": f"Failed to delete file: {str(e)}"}, HTTP_400_BAD_REQUEST


# Route to list files in the MinIO bucket
@get("/list-files")
async def list_files() -> list:
    try:
        files = minio_client.list_objects(MINIO_BUCKET_NAME)
        file_names = [obj.object_name for obj in files]
        return file_names
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        return []


# Configure the Litestar app
app = Litestar(
    route_handlers=[home, start_scraper, sse_logs, upload_file, delete_file, list_files],
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
    ),
    request_max_body_size=1024 * 1024 * 1024  # 1GB upload limit
)