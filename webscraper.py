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
from minio_utils import minio_client, ensure_bucket_exists, upload_to_minio, download_from_minio
from data_processor import process_tsv
from db import insert_patient_data

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

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
    os.remove(gz_file)
    logger.info(f"Removed {gz_file}")

def scrape_tcga_data():
    base_url = "https://xenabrowser.net/datapages/?hub=https://tcga.xenahubs.net:443"
    output_dir = "cohorts"
    
    ensure_bucket_exists()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Failed to delete {file_path}. Reason: {e}")
    
    driver = setup_driver()
    
    try:
        logger.info(f"Navigating to {base_url}")
        driver.get(base_url)
        time.sleep(5)
        
        cohort_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'cohort=TCGA')]")
        logger.info(f"Found {len(cohort_links)} cohort links")

        for cohort_link in cohort_links:
            cohort_name = cohort_link.text.split('(')[0].strip()
            cohort_url = cohort_link.get_attribute('href')
            logger.info(f"Processing cohort: {cohort_name}")

            try:
                driver.execute_script("window.open();")
                driver.switch_to.window(driver.window_handles[-1])
                driver.get(cohort_url)
                time.sleep(5)

                pancan_link = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "IlluminaHiSeq pancan normalized"))
                )
                pancan_link.click()

                download_link = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='.gz']"))
                )
                download_url = download_link.get_attribute('href')

                gz_file_name = os.path.join(output_dir, f"{cohort_name.replace(' ', '_')}_HiSeqV2_PANCAN.gz")
                tsv_file_name = gz_file_name.replace(".gz", ".tsv")

                download_file(download_url, gz_file_name)
                decompress_gz_to_tsv(gz_file_name, tsv_file_name)

                object_name = os.path.basename(tsv_file_name)
                if upload_to_minio(tsv_file_name, object_name):
                    # Process and store in MongoDB
                    temp_path = f"temp_{object_name}"
                    if download_from_minio(object_name, temp_path):
                        patients = process_tsv(temp_path)
                        for patient in patients:
                            insert_patient_data(patient)
                        os.remove(temp_path)
                    
                    os.remove(tsv_file_name)
                    logger.info(f"Removed local file: {tsv_file_name}")

            except (TimeoutException, NoSuchElementException) as e:
                logger.error(f"Error processing {cohort_name}: {str(e)}")
            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

    except WebDriverException as e:
        logger.error(f"WebDriver exception: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_tcga_data()