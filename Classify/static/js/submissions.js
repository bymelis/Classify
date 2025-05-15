let currentSubmissionId;

function viewSubmissionDetails(submissionId) {
    currentSubmissionId = submissionId;
    const modal = document.getElementById('submissionModal');
    modal.dataset.submissionId = submissionId;

    fetch(`/get_submission/${submissionId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('modalTitle').textContent = data.assignment_title;
            document.getElementById('modalContent').innerHTML = `
                <div class="submission-meta">
                    <p><strong>Student:</strong> ${data.student_name}</p>
                    <p><strong>Submitted:</strong> ${new Date(data.submitted_at).toLocaleString()}</p>
                </div>
                <div class="submission-content">
                    <div class="notes-section">
                        <h4>Student's Notes:</h4>
                        <p>${data.content || 'No notes provided'}</p>
                    </div>

                    <div class="action-buttons">
                        ${data.file_path ? `
                            <a href="/download_submission/${data.id}" class="action-btn download-btn">
                                <i class="fas fa-download"></i> Download Attachment
                            </a>
                        ` : ''}
                        <button onclick="checkPlagiarism(${submissionId})" class="action-btn plagiarism-btn">
                            <i class="fas fa-search"></i> Check for Plagiarism
                        </button>
                    </div>

                    <div id="plagiarismResults" class="plagiarism-results" style="display: none;">
                        <h3>Plagiarism Results</h3>
                        <div id="plagiarismContent"></div>
                    </div>
                </div>
            `;

            // Set up grade form
            document.getElementById('grade').value = data.grade !== null ? data.grade : '';
            document.getElementById('feedback').value = data.feedback || '';

            modal.style.display = 'block';
        });
}

function closeModal() {
    document.getElementById('submissionModal').style.display = 'none';
    document.getElementById('gradeForm').reset();
    // Reset plagiarism results when closing modal
    const plagiarismResults = document.getElementById('plagiarismResults');
    if (plagiarismResults) {
        plagiarismResults.style.display = 'none';
    }
}

async function checkPlagiarism(submissionId) {
    const plagiarismResults = document.getElementById('plagiarismResults');
    const plagiarismContent = document.getElementById('plagiarismContent');
    const button = event.target;

    try {
        // Update UI to loading state
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
        plagiarismContent.innerHTML = '<p>Initiating plagiarism check...</p>';
        plagiarismResults.style.display = 'block';

        const response = await fetch(`/check_plagiarism/${submissionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.status === 'success') {
            plagiarismContent.innerHTML = '<p>Plagiarism check initiated. Getting results...</p>';
            pollPlagiarismResults(submissionId);
        } else {
            throw new Error(data.message || 'Failed to initiate plagiarism check');
        }
    } catch (error) {
        console.error('Error:', error);
        plagiarismContent.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    } finally {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-search"></i> Check for Plagiarism';
    }
}

async function pollPlagiarismResults(submissionId) {
    const plagiarismContent = document.getElementById('plagiarismContent');
    const maxAttempts = 30;
    let attempts = 0;

    const poll = setInterval(async () => {
        try {
            attempts++;
            const response = await fetch(`/plagiarism_results/${submissionId}`);
            const data = await response.json();

            if (data.status === 'completed') {
                clearInterval(poll);
                displayPlagiarismResults(data.results);
            } else if (data.status === 'error') {
                clearInterval(poll);
                throw new Error(data.message);
            } else if (attempts >= maxAttempts) {
                clearInterval(poll);
                throw new Error('Plagiarism check timed out. Please try again later.');
            } else {
                plagiarismContent.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Still checking... Please wait...</p>';
            }
        } catch (error) {
            clearInterval(poll);
            plagiarismContent.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        }
    }, 5000); // Poll every 5 seconds
}

function displayPlagiarismResults(results) {
    const plagiarismContent = document.getElementById('plagiarismContent');

    let html = '<div class="plagiarism-results-summary">';
    if (results.matches && results.matches.length > 0) {
        html += `
            <div class="alert alert-warning">
                <h4>Found ${results.matches.length} potential matches:</h4>
                <ul class="matches-list">
                    ${results.matches.map(match => `
                        <li class="match-item">
                            <div class="match-title">${match.title || 'Unnamed Source'}</div>
                            <div class="match-similarity">${match.similarity}% similar</div>
                            ${match.url ? `<div class="match-url"><a href="${match.url}" target="_blank">View Source</a></div>` : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>`;
    } else {
        html += '<div class="alert alert-success">No significant matches found.</div>';
    }
    html += '</div>';

    plagiarismContent.innerHTML = html;
}

// Grade submission handling
document.getElementById('gradeForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData();
    formData.append('submission_id', currentSubmissionId);
    formData.append('grade', document.getElementById('grade').value);
    formData.append('feedback', document.getElementById('feedback').value);

    fetch('/grade_submission', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to submit grade');
    });
});

function dismissMainFlash() {
    const flashMessage = document.getElementById('main-flash-message');
    if (flashMessage) {
        flashMessage.style.opacity = '0';
        setTimeout(() => flashMessage.style.display = 'none', 300);
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        closeModal();
    }
};
function showAllSubmissions(assignmentId) {
    const modal = document.getElementById('allSubmissionsModal');

    // Fetch all submissions for this assignment
    fetch(`/get_all_submissions/${assignmentId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('assignmentTitle').textContent = 'All Submissions';
            const submissionsList = document.getElementById('submissionsList');

            // Clear previous content
            submissionsList.innerHTML = '';

            // Add each submission
            data.forEach(submission => {
                const submissionEl = document.createElement('div');
                submissionEl.className = 'submission-item';
                submissionEl.onclick = () => viewSubmissionDetails(submission.id);

                // Format date in a more concise way
                const submittedDate = new Date(submission.submitted_at);
                const dateString = submittedDate.toLocaleDateString();
                const timeString = submittedDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

                submissionEl.innerHTML = `
                    <div class="submission-item-content">
                        <div class="student-name">${submission.student_name}</div>
                        <div class="submission-meta">
                            <span class="submission-date">${dateString}, ${timeString}</span>
                            ${submission.grade !== null ? 
                                `<span class="grade-badge graded">${submission.grade}/100</span>` : 
                                `<span class="grade-badge pending">Not Graded</span>`
                            }
                        </div>
                    </div>
                `;

                submissionsList.appendChild(submissionEl);
            });

            modal.style.display = 'block';
        });
}

function closeAllSubmissionsModal() {
    document.getElementById('allSubmissionsModal').style.display = 'none';
}

// Update the window click handler to handle both modals
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
};
