# data_processor.py
from db import client
from minio_utils import minio_client, MINIO_BUCKET_NAME
import csv
from io import StringIO

TARGET_GENES = {
    'C6orf150', 'CCL5', 'CXCL10', 'TMEM173', 'CXCL9',
    'CXCL11', 'NFKB1', 'IKBKE', 'IRF3', 'TREX1', 'ATM', 'IL6', 'IL8'
}

def process_tsv_from_minio(object_name):
    try:
        cancer_cohort = f"TCGA-{object_name.split('_')[0]}"
        response = minio_client.get_object(MINIO_BUCKET_NAME, object_name)
        data = response.read().decode('utf-8')
        reader = csv.reader(StringIO(data), delimiter='\t')
        
        headers = next(reader)
        patient_ids = headers[1:]
        patients = {pid: {'patient_id': pid, 'cancer_cohort': cancer_cohort, 'gene_expressions': {}} for pid in patient_ids}
        
        for row in reader:
            gene = row[0].strip()
            if gene in TARGET_GENES:
                for i, value in enumerate(row[1:]):
                    pid = patient_ids[i]
                    try:
                        patients[pid]['gene_expressions'][gene] = float(value) if value else None
                    except ValueError:
                        pass
        
        db = client.gene_database
        collection = db.patients
        for pid, data in patients.items():
            collection.update_one(
                {'patient_id': pid},
                {'$set': data},
                upsert=True
            )
        print(f"Processed {object_name}")
    except Exception as e:
        print(f"Error processing {object_name}: {str(e)}")