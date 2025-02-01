from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
import logging
import os
import pandas as pd

logger = logging.getLogger(__name__)

uri = os.getenv("MONGO_URI", "mongodb+srv://lenno:lenno@cluster0.p5luf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

try:
    client = MongoClient(uri, tlsCAFile=certifi.where(), server_api=ServerApi('1'))
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB!")
    
    db = client['gene_expression_db']
    patients_collection = db['patients']
    
except Exception as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    raise

def load_clinical_data(file_path='static/TCGA_clinical_survival_data.tsv'):
    """
    Load and process clinical survival data from TSV file.
    Returns a dictionary with patient barcodes (without -XX suffix) as keys.
    """
    try:
        clinical_df = pd.read_csv(file_path, sep='\t')
        clinical_data = {}
        
        for _, row in clinical_df.iterrows():
            # Remove the -XX suffix from the barcode (e.g., -01)
            base_barcode = row['bcr_patient_barcode'].split('-', 3)
            if len(base_barcode) >= 3:
                base_barcode = '-'.join(base_barcode[:3])
                clinical_data[base_barcode] = {
                    'DSS': int(row['DSS']) if pd.notna(row['DSS']) else None,
                    'OS': int(row['OS']) if pd.notna(row['OS']) else None,
                    'clinical_stage': row['clinical_stage'] if pd.notna(row['clinical_stage']) else None
                }
        
        logger.info(f"Loaded clinical data for {len(clinical_data)} patients")
        return clinical_data
    except Exception as e:
        logger.error(f"Error loading clinical data: {str(e)}")
        return {}

# Global variable to store clinical data
clinical_data_cache = None

def get_clinical_data():
    """
    Get clinical data, loading it from file if not already cached
    """
    global clinical_data_cache
    if clinical_data_cache is None:
        clinical_data_cache = load_clinical_data()
    return clinical_data_cache

def insert_patient_data(patient_data: dict):
    try:
        # Get the base patient ID (without -XX suffix)
        patient_id = patient_data["patient_id"]
        base_patient_id = '-'.join(patient_id.split('-', 3)[:3])
        
        # Get clinical data for this patient
        clinical_data = get_clinical_data()
        if base_patient_id in clinical_data:
            patient_data.update({
                'DSS': clinical_data[base_patient_id]['DSS'],
                'OS': clinical_data[base_patient_id]['OS'],
                'clinical_stage': clinical_data[base_patient_id]['clinical_stage']
            })
        else:
            logger.warning(f"No clinical data found for patient {base_patient_id}")
            # Add null values for clinical fields
            patient_data.update({
                'DSS': None,
                'OS': None,
                'clinical_stage': None
            })
        
        result = patients_collection.update_one(
            {"patient_id": patient_data["patient_id"], "cancer_cohort": patient_data["cancer_cohort"]},
            {"$set": patient_data},
            upsert=True
        )
        
        if result.upserted_id:
            logger.info(f"Inserted new patient: {patient_data['patient_id']} with clinical data")
        else:
            logger.debug(f"Updated existing patient: {patient_data['patient_id']} with clinical data")
        return True
        
    except Exception as e:
        logger.error(f"Error inserting patient {patient_data.get('patient_id', 'unknown')}: {str(e)}")
        return False