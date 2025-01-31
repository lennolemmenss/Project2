from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi
import logging

logger = logging.getLogger(__name__)

uri = "mongodb+srv://lenno:lenno@cluster0.p5luf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(uri, tlsCAFile=certifi.where(), server_api=ServerApi('1'))
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB!")
    
    db = client['gene_expression_db']
    patients_collection = db['patients']
    
except Exception as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    raise

def insert_patient_data(patient_data: dict):
    try:
        result = patients_collection.update_one(
            {"patient_id": patient_data["patient_id"], "cancer_cohort": patient_data["cancer_cohort"]},
            {"$set": patient_data}, 
            upsert=True
        )
        if result.upserted_id:
            logger.info(f"Inserted new patient: {patient_data['patient_id']}")
        else:
            logger.debug(f"Updated existing patient: {patient_data['patient_id']}")
        return True
    except Exception as e:
        logger.error(f"Error inserting patient {patient_data.get('patient_id', 'unknown')}: {str(e)}")
        return False