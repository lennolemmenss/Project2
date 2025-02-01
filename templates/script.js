document.getElementById("start-scraper").addEventListener("click", async () => {
    const button = document.getElementById("start-scraper");
    const message = document.getElementById("message");
    const logsDiv = document.getElementById("logs");

    button.disabled = true;
    button.textContent = "Scraping...";
    message.textContent = "";
    logsDiv.innerHTML = "<pre class='text-sm text-gray-700 font-mono'>Logs will appear here...</pre>";
    
    try {
        const response = await fetch("/start-scraper", {
            method: "POST",
        });

        if (response.ok) {
            const data = await response.json();
            message.textContent = data.message;

            const eventSource = new EventSource("/logs");
            eventSource.onmessage = (event) => {
                const logEntry = document.createElement("div");
                logEntry.textContent = event.data;
                logEntry.classList.add("text-sm", "text-gray-700", "font-mono");
                logsDiv.appendChild(logEntry);
                logsDiv.scrollTop = logsDiv.scrollHeight;
            };
        } else {
            message.textContent = "Failed to start the scraper.";
        }
    } catch (error) {
        message.textContent = "An error occurred.";
    } finally {
        button.disabled = false;
        button.textContent = "Start Scraper";
    }
});

// Function to fetch and display the list of uploaded files
async function fetchFileList() {
    const fileListDiv = document.getElementById("file-list");
    try {
        const response = await fetch("/list-files");
        if (response.ok) {
            const files = await response.json();
            fileListDiv.innerHTML = files.map(file => `
                <div class="flex justify-between items-center p-2 border-b border-gray-300">
                    <span>${file}</span>
                    <button
                        onclick="deleteFile('${file}')"
                        class="bg-red-500 text-white px-3 py-1 rounded-lg hover:bg-red-600 transition duration-300"
                    >
                        Delete
                    </button>
                </div>
            `).join("");
        } else {
            fileListDiv.innerHTML = "<p class='text-red-500'>Failed to fetch file list.</p>";
        }
    } catch (error) {
        fileListDiv.innerHTML = "<p class='text-red-500'>An error occurred while fetching the file list.</p>";
    }
}

// Function to delete a file
async function deleteFile(fileName) {
    try {
        const response = await fetch("/delete-file", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ file_name: fileName }),
        });

        if (response.ok) {
            alert(`File ${fileName} deleted successfully!`);
            fetchFileList(); // Refresh the file list
        } else {
            alert(`Failed to delete file ${fileName}.`);
        }
    } catch (error) {
        alert("An error occurred while deleting the file.");
    }
}

// Function to handle file upload
document.getElementById("upload-button").addEventListener("click", () => {
    document.getElementById("file-upload").click();
});

document.getElementById("file-upload").addEventListener("change", async (event) => {
    console.log(event.target.files);
    console.log("check frontend");

    const file = event.target.files[0];
    if (file) {
        const formData = new FormData();
        formData.append("file", file);  // Ensure the key is "file"
        console.log(formData);

        try {
            const response = await fetch("/upload-file", {
                method: "POST",
                body: formData,  // No headers needed for FormData
            });

            if (response.ok) {
                alert(`File ${file.name} uploaded successfully!`);
                fetchFileList();  // Refresh the file list
            } else {
                const errorData = await response.json();
                console.log(errorData);
                alert(`Failed to upload file: ${errorData.message}`);
            }
        } catch (error) {
            alert("An error occurred while uploading the file.");
        }
    }
});

async function initializeCohortSelect() {
    const select = document.getElementById('cohort-select');
    try {
        const response = await fetch('/patients');
        if (response.ok) {
            const data = await response.json();
            const uniqueCohorts = [...new Set(data.map(p => p.cancer_cohort))].sort();
            
            select.innerHTML = '<option value="">Choose a cohort</option>' +
                uniqueCohorts.map(cohort => 
                    `<option value="${cohort}">${cohort}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error fetching cohorts:', error);
    }
}

async function fetchAndDisplayPatients(cohort) {
    const tableContainer = document.getElementById('patient-table-container');
    const table = document.getElementById('patient-table');
    const loading = document.getElementById('patient-loading');
    const empty = document.getElementById('patient-empty');
    
    table.classList.add('hidden');
    empty.classList.add('hidden');
    loading.classList.remove('hidden');
    
    try {
        const response = await fetch(`/patients/${encodeURIComponent(cohort)}`);
        if (response.ok) {
            const patients = await response.json();
            
            if (patients.length === 0) {
                loading.classList.add('hidden');
                empty.classList.remove('hidden');
                return;
            }
            
            // Get gene columns (excluding patient_id and cancer_cohort)
            const geneColumns = Object.keys(patients[0])
                .filter(key => !['patient_id', 'cancer_cohort'].includes(key));
            
            // Update header
            const headerRow = table.querySelector('thead tr');
            headerRow.innerHTML = `
                <th class="p-2 border text-left">Patient ID</th>
                ${geneColumns.map(gene => 
                    `<th class="p-2 border text-left">${gene}</th>`
                ).join('')}
            `;
            
            // Update body
            const tbody = table.querySelector('tbody');
            tbody.innerHTML = patients.map((patient, index) => `
                <tr class="${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">
                    <td class="p-2 border font-medium">${patient.patient_id}</td>
                    ${geneColumns.map(gene => 
                        `<td class="p-2 border">${
                            typeof patient[gene] === 'number' 
                                ? patient[gene].toFixed(2) 
                                : patient[gene]
                        }</td>`
                    ).join('')}
                </tr>
            `).join('');
            
            loading.classList.add('hidden');
            table.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error fetching patients:', error);
        loading.classList.add('hidden');
        empty.classList.remove('hidden');
    }
}

// Initialize cohort select when page loads
initializeCohortSelect();

// Add event listener for cohort selection
document.getElementById('cohort-select').addEventListener('change', (e) => {
    const selectedCohort = e.target.value;
    if (selectedCohort) {
        fetchAndDisplayPatients(selectedCohort);
    } else {
        document.getElementById('patient-table').classList.add('hidden');
        document.getElementById('patient-empty').classList.add('hidden');
    }
});



// Patient Data Viewer functionality
let allPatients = []; // Store all patients for filtering

async function initializeCohortSelect() {
    const select = document.getElementById('cohort-select');
    try {
        const response = await fetch('/patients');
        if (response.ok) {
            const data = await response.json();
            const uniqueCohorts = [...new Set(data.map(p => p.cancer_cohort))].sort();
            
            select.innerHTML = '<option value="">Choose a cohort</option>' +
                uniqueCohorts.map(cohort => 
                    `<option value="${cohort}">${cohort}</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error fetching cohorts:', error);
    }
}

function filterAndDisplayPatients() {
    const filterValue = document.getElementById('patient-filter').value.toLowerCase();
    const filteredPatients = allPatients.filter(patient => 
        patient.patient_id.toLowerCase().includes(filterValue)
    );
    updatePatientTable(filteredPatients);
}

function updatePatientTable(patients) {
    const table = document.getElementById('patient-table');
    const empty = document.getElementById('patient-empty');
    
    if (patients.length === 0) {
        table.classList.add('hidden');
        empty.classList.remove('hidden');
        return;
    }
    
    // Get gene columns (excluding patient_id and cancer_cohort)
    const geneColumns = Object.keys(patients[0])
        .filter(key => !['patient_id', 'cancer_cohort'].includes(key));
    
    // Update header
    const headerRow = table.querySelector('thead tr');
    headerRow.innerHTML = `
        <th class="p-2 border text-left">Patient ID</th>
        ${geneColumns.map(gene => 
            `<th class="p-2 border text-left">${gene}</th>`
        ).join('')}
    `;
    
    // Update body
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = patients.map((patient, index) => `
        <tr class="${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}">
            <td class="p-2 border font-medium">${patient.patient_id}</td>
            ${geneColumns.map(gene => 
                `<td class="p-2 border">${
                    typeof patient[gene] === 'number' 
                        ? patient[gene].toFixed(2) 
                        : patient[gene]
                }</td>`
            ).join('')}
        </tr>
    `).join('');
    
    empty.classList.add('hidden');
    table.classList.remove('hidden');
}

async function fetchAndDisplayPatients(cohort) {
    const table = document.getElementById('patient-table');
    const loading = document.getElementById('patient-loading');
    const empty = document.getElementById('patient-empty');
    const patientFilter = document.getElementById('patient-filter');
    
    table.classList.add('hidden');
    empty.classList.add('hidden');
    loading.classList.remove('hidden');
    patientFilter.value = ''; // Clear filter when changing cohort
    
    try {
        const response = await fetch(`/patients/${encodeURIComponent(cohort)}`);
        if (response.ok) {
            allPatients = await response.json(); // Store all patients
            loading.classList.add('hidden');
            filterAndDisplayPatients(); // Initial display
        }
    } catch (error) {
        console.error('Error fetching patients:', error);
        loading.classList.add('hidden');
        empty.classList.remove('hidden');
    }
}

// Initialize cohort select when page loads
initializeCohortSelect();

// Add event listeners
document.getElementById('cohort-select').addEventListener('change', (e) => {
    const selectedCohort = e.target.value;
    if (selectedCohort) {
        fetchAndDisplayPatients(selectedCohort);
    } else {
        document.getElementById('patient-table').classList.add('hidden');
        document.getElementById('patient-empty').classList.add('hidden');
        document.getElementById('patient-filter').value = '';
        allPatients = [];
    }
});

// Add event listener for patient ID filter
document.getElementById('patient-filter').addEventListener('input', (e) => {
    filterAndDisplayPatients();
});
                
        

// Fetch the file list when the page loads
fetchFileList();

setInterval(() => {
fetchFileList();
}, 5000);

