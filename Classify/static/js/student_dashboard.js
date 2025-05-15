const current_user_role = 'student';

function openAssignmentModal(assignmentId) {
    fetch(`/get_assignment/${assignmentId}`)
        .then(response => response.json())
        .then(assignment => {
            if (assignment.submission) {
                if (assignment.submission.grade !== null) {
                    showGradedAssignment(assignment);
                } else {
                    showSubmittedNotification();
                }
            } else {
                showSubmissionModal(assignment);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading assignment details');
        });
}

function showGradedAssignment(assignment) {
    const modal = document.getElementById('gradedAssignmentModal');
    const submission = assignment.submission;

    // Update assignment details
    document.getElementById('assignmentTitle').textContent = assignment.title;
    document.getElementById('assignmentClass').textContent = assignment.class_name;

    // Update grade
    document.getElementById('gradeValue').textContent = submission.grade;
    document.getElementById('maxPoints').textContent = assignment.points;

    // Update feedback
    const feedbackContent = document.getElementById('feedbackContent');
    feedbackContent.textContent = submission.feedback || 'No feedback provided';

    // Format dates nicely
    const submissionDate = new Date(submission.submitted_at);
    const gradingDate = submission.graded_at ? new Date(submission.graded_at) : null;

    document.getElementById('submissionDate').textContent = submissionDate.toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short'
    });

    document.getElementById('gradingDate').textContent = gradingDate
        ? gradingDate.toLocaleString(undefined, {
            dateStyle: 'medium',
            timeStyle: 'short'
        })
        : 'Not available';

    // Update download link
    const downloadLink = document.getElementById('downloadSubmissionLink');
    if (submission.file_path) {
        downloadLink.href = `/download_submission/${assignment.id}`;
        downloadLink.style.display = 'flex';
    } else {
        downloadLink.style.display = 'none';
    }

    modal.style.display = 'block';
}

function showSubmittedNotification() {
    const notification = document.createElement('div');
    notification.className = 'flash-message';
    notification.innerHTML = `
        <div class="alert alert-info">
            Your assignment has been submitted and is pending grading.
            <button class="close-btn" onclick="this.parentElement.remove()">&times;</button>
        </div>
    `;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function showSubmissionModal(assignment) {
    const modal = document.getElementById('assignmentModal');
    document.getElementById('assignmentId').value = assignment.id;
    modal.style.display = 'block';
}

function closeGradedAssignmentModal() {
    document.getElementById('gradedAssignmentModal').style.display = 'none';
}

function closeAssignmentModal() {
    document.getElementById('assignmentModal').style.display = 'none';
    document.getElementById('assignmentForm').reset();
}

document.getElementById('assignmentForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const formData = new FormData(this);

    fetch('/submit_assignment', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeAssignmentModal();
            location.reload();
        } else {
            alert(data.error || 'Error submitting assignment');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error submitting assignment');
    });
});

function dismissMainFlash() {
    const flashMessage = document.getElementById('main-flash-message');
    if (flashMessage) {
        flashMessage.style.opacity = '0';
        setTimeout(() => {
            flashMessage.style.display = 'none';
        }, 300);
    }
}

window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const flashMessage = document.getElementById('main-flash-message');
    if (flashMessage) {
        setTimeout(() => {
            dismissMainFlash();
        }, 5000);
    }
});