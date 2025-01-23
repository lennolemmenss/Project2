from pathlib import Path
from litestar import Litestar, get, post
from litestar.response import Template
from litestar.template import TemplateConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Stream
import subprocess
import threading
import queue
import logging
import asyncio

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

# Configure the Litestar app
app = Litestar(
    route_handlers=[home, start_scraper, sse_logs],
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
    ),
)