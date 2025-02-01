# Overview
This project is a web scraper designed to download, process, and store gene expression data from the TCGA (The Cancer Genome Atlas) database. The data is downloaded in `.gz` format, decompressed to `.tsv`, and then uploaded to a MinIO storage bucket. The processed data is also stored in a MongoDB database for further analysis and visualization.

The project includes a web interface built with Litestar (a Python web framework) and Tailwind CSS for styling. The interface allows users to:
- Start the web scraper.
- View uploaded TSV files.
- Explore patient data, including gene expression and clinical information.
- Visualize clinical data and gene expression using Plotly.

## Features
### 1. Web Scraper
- Automatically downloads IlluminaHiSeq pancan normalized gene files from the TCGA database.
- Converts `.gz` files to `.tsv` format.
- Uploads processed files to MinIO for storage.
- Processes and stores patient data in MongoDB.

### 2. File Management
- Users can upload `.tsv` files manually.
- Uploaded files are stored in MinIO and processed for patient data.
- Users can delete files from MinIO.

### 3. Patient Data Viewer
- View patient data by selecting a cancer cohort.
- Filter patients by Patient ID or Clinical Stage.
- View clinical data such as Overall Survival (OS), Disease-Specific Survival (DSS), and Clinical Stage.

### 4. Clinical Data Visualization
- **Survival Rate by Clinical Stage**: Bar chart showing survival rates for different clinical stages.
- **DSS Distribution**: Pie chart showing the distribution of Disease-Specific Survival.

### 5. Gene Expression Visualization
- Visualize gene expression levels for selected genes across patients.
- Bar chart showing expression levels for a specific gene.

## Technologies Used
### Backend
- **Litestar**: Python web framework for building the API and serving the frontend.
- **MinIO**: Object storage for storing `.tsv` files.
- **MongoDB**: Database for storing processed patient data.
- **Selenium**: Web scraping tool for downloading TCGA data.
- **Pandas**: Data processing library for handling `.tsv` files.

### Frontend
- **Tailwind CSS**: Utility-first CSS framework for styling.
- **Plotly**: JavaScript library for interactive data visualization.
- **JavaScript**: For dynamic updates and interactivity.

## Setup Instructions
### 1. Prerequisites
- Docker and Docker Compose installed.
- Python 3.8+ installed.

### 2. Clone the Repository
```bash
git clone https://github.com/your-repo/tcga-web-scraper.git
cd tcga-web-scraper
```

### 4. Run with Docker
```bash
docker-compose up --build
```
This will start the following services:
- **App**: The Litestar web application.
- **Minio**: MinIO object storage.
- **Selenium**: Webscraper.

### 5. Access the Application
Open your browser and navigate to `http://localhost:8000`.

## Usage
### 1. Start the Scraper
Click the **Start Scraper** button to begin downloading and processing TCGA data. Logs will appear in the Logs section.

### 2. Upload TSV Files
Click the **Upload TSV File** button to upload a `.tsv` file manually. Uploaded files will appear in the Uploaded TSV Files section.

### 3. View Patient Data
Select a cancer cohort from the dropdown menu. Use the **Filter Patient ID** and **Clinical Stage Filter** to refine the results. Patient data will be displayed in a table.

### 4. Visualize Data
View **Survival Rate by Clinical Stage** and **DSS Distribution** in the Clinical Data Analysis section. Select a gene from the dropdown menu to visualize gene expression levels.

## File Structure
```plaintext
tcga-web-scraper/
├── app/
│   ├── main.py              # Litestar application and routes
│   ├── data_processor.py    # Process .tsv files and extract gene data
│   ├── db.py                # MongoDB connection and patient data insertion
│   ├── minio_utils.py       # MinIO utility functions
│   ├── webscraper.py        # Selenium-based web scraper
├── templates/
│   ├── index.html           # Frontend HTML template
├── docker-compose.yml       # Docker Compose configuration
├── requirements.txt         # Python dependencies
```

## API Endpoints
### 1. Web Scraper
- `POST /start-scraper`: Start the web scraper.
- `GET /logs`: Stream logs in real-time using Server-Sent Events (SSE).

### 2. File Management
- `POST /upload-file`: Upload a `.tsv` file.
- `POST /delete-file`: Delete a file from MinIO.
- `GET /list-files`: List all files in the MinIO bucket.

### 3. Patient Data
- `GET /patients`: List all patients.
- `GET /patients/{cancer_cohort}`: List patients by cancer cohort.
- `GET /patient/{patient_id}`: Get patient details by ID.
