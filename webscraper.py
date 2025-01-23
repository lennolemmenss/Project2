import os
import time
import requests
import gzip
import shutil
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from minio import Minio  # Import MinIO SDK

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# MinIO configuration
MINIO_ENDPOINT = "localhost:9000"  # MinIO server address
MINIO_ACCESS_KEY = "minioadmin"    # MinIO access key
MINIO_SECRET_KEY = "minioadmin"    # MinIO secret key
MINIO_BUCKET_NAME = "gene-data"    # MinIO bucket name

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Set to True if using HTTPS
)

def setup_driver(): 
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def download_file(url, destination):
    response = requests.get(url)
    with open(destination, 'wb') as file:
        file.write(response.content)

def decompress_gz_to_tsv(gz_file, tsv_file):
    with gzip.open(gz_file, 'rb') as f_in:
        with open(tsv_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    logger.info(f"Decompressed {gz_file} to {tsv_file}")
    os.remove(gz_file)  # Remove the .gz file
    logger.info(f"Removed {gz_file}")

def upload_to_minio(file_path, bucket_name, object_name):
    try:
        minio_client.fput_object(
            bucket_name,
            object_name,
            file_path
        )
        logger.info(f"Uploaded {file_path} to MinIO as {object_name}")
    except Exception as e:
        logger.error(f"Failed to upload {file_path} to MinIO: {str(e)}")


def scrape_tcga_data():
    base_url = "https://xenabrowser.net/datapages/?hub=https://tcga.xenahubs.net:443"
    

    # Ensure the bucket exists
    if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
        minio_client.make_bucket(MINIO_BUCKET_NAME)
        logger.info(f"Created MinIO bucket: {MINIO_BUCKET_NAME}")

    # Create the 'cohorts' directory if it doesn't exist
    output_dir = "cohorts"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created directory: {output_dir}")
    
    else:
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    logger.info(f"Removed file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    logger.info(f"Removed directory: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}. Reason: {e}")
    
    driver = setup_driver()
    
    try:
        logger.info(f"Navigating to {base_url}")
        driver.get(base_url)
        
        # Wait for the page to load
        time.sleep(5)
        
        logger.info("Attempting to find cohort links...")
        cohort_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'cohort=TCGA')]")
        
        logger.info(f"Found {len(cohort_links)} cohort links")

        for cohort_link in cohort_links:
            cohort_name = cohort_link.text.split('(')[0].strip()
            cohort_url = cohort_link.get_attribute('href')
            logger.info(f"Processing cohort: {cohort_name}")

            try:
                # Open cohort page in a new tab
                driver.execute_script("window.open();")
                driver.switch_to.window(driver.window_handles[-1])
                driver.get(cohort_url)
                
                # Wait for the page to load
                time.sleep(5)

                # Find and click the "IlluminaHiSeq pancan normalized" link
                pancan_link = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "IlluminaHiSeq pancan normalized"))
                )
                pancan_link.click()

                # Find the download link
                download_link = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='.gz']"))
                )
                download_url = download_link.get_attribute('href')

                # Set the file paths inside the 'cohorts' directory
                gz_file_name = os.path.join(output_dir, f"{cohort_name.replace(' ', '_')}_HiSeqV2_PANCAN.gz")
                tsv_file_name = gz_file_name.replace(".gz", ".tsv")

                # Download the file
                download_file(download_url, gz_file_name)
                logger.info(f"Downloaded: {gz_file_name}")

                # Decompress the .gz file to a .tsv file
                decompress_gz_to_tsv(gz_file_name, tsv_file_name)

                # Upload the .tsv file to MinIO
                object_name = os.path.basename(tsv_file_name)
                upload_to_minio(tsv_file_name, MINIO_BUCKET_NAME, object_name)

                # Remove the .tsv file from local storage after uploading
                os.remove(tsv_file_name)
                logger.info(f"Removed local file: {tsv_file_name}")

            except (TimeoutException, NoSuchElementException) as e:
                logger.error(f"Error occurred while processing {cohort_name}: {str(e)}")
            finally:
                # Close the tab and switch back to the main window
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

    except WebDriverException as e:
        logger.error(f"WebDriver exception occurred: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_tcga_data()