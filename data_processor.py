import pandas as pd
import os
import logging
import re

logger = logging.getLogger(__name__)

# Primary gene names and their alternatives
GENE_ALTERNATIVES = {
    "C6orf150": ["cGAS"],
    "TMEM173": ["STING"],
    "IL8": ["CXCL8"]
}

# Target genes (primary names)
TARGET_GENES = [
    "C6orf150", "CCL5", "CXCL10", "TMEM173", "CXCL9",
    "CXCL11", "NFKB1", "IKBKE", "IRF3", "TREX1", "ATM", "IL6", "IL8"
]

def extract_cancer_cohort(file_name: str) -> str:
    try:
        # Remove file extension
        file_name = os.path.splitext(file_name)[0]
        
        # Extract cohort name using regex
        match = re.search(r"TCGA_(.+?)_HiSeqV2_PANCAN", file_name)
        if match:
            cohort = match.group(1).replace("_", " ")
            return cohort
        else:
            logger.warning(f"Could not extract cancer cohort from file name: {file_name}")
            return "Unknown"
    except Exception as e:
        logger.error(f"Error extracting cancer cohort: {str(e)}")
        return "Unknown"

def find_gene_column(df: pd.DataFrame, gene: str) -> str:
    """
    Finds the column name for a gene, checking primary and alternative names.
    Returns None if the gene is not found.
    """
    # Check primary name
    if gene in df.columns:
        return gene
    
    # Check alternative names
    alternatives = GENE_ALTERNATIVES.get(gene, [])
    for alt in alternatives:
        if alt in df.columns:
            return alt
    
    # Gene not found
    return None

def process_tsv(file_path: str) -> list[dict]:
    """Extracts gene expression data for target genes."""
    try:
        logger.info(f"Processing file: {file_path}")
        
        # Read TSV with error handling
        df = pd.read_csv(file_path, sep='\t', index_col=0, on_bad_lines='warn')
        logger.info(f"TSV shape: {df.shape}")
        
        # Extract cancer cohort from file name
        file_name = os.path.basename(file_path)
        cancer_cohort = extract_cancer_cohort(file_name)
        logger.info(f"Detected cancer cohort: {cancer_cohort}")

        # Transpose and clean data
        df = df.T.reset_index().rename(columns={'index': 'patient_id'})
        logger.info(f"Unique patients: {df['patient_id'].nunique()}")

        # Filter target genes
        available_genes = {}
        missing_genes = set()
        
        for gene in TARGET_GENES:
            column_name = find_gene_column(df, gene)
            if column_name:
                available_genes[gene] = column_name
            else:
                missing_genes.add(gene)
        
        if missing_genes:
            logger.warning(f"Missing genes in this file: {missing_genes}")

        # Select columns for available genes
        df = df[['patient_id'] + list(available_genes.values())]
        
        # Rename columns to primary gene names
        df = df.rename(columns={v: k for k, v in available_genes.items()})
        
        # Add cancer cohort
        df['cancer_cohort'] = cancer_cohort

        # Convert to list of documents
        patients = df.to_dict('records')
        logger.info(f"Processed {len(patients)} patients")
        
        # Print first patient as sample
        if patients:
            logger.info(f"Sample patient data: {patients[0]}")
            
        return patients

    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return []