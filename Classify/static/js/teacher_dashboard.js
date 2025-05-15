let currentAssignmentId;

// Open create assignment modal
function openModal() {
    document.getElementById('createModal').style.display = 'block';
}

// Close create assignment modal
function closeModal() {
    document.getElementById('createModal').style.display = 'none';
    document.querySelector('#createModal form').reset();
}

// Open assignment details modal for updating
function openAssignmentModal(assignmentId) {
    currentAssignmentId = assignmentId;
    document.getElementById('assignmentModal').style.display = 'block';

    // Get the assignment card data
    const assignmentCard = document.querySelector(`.assignment-card[onclick*="${assignmentId}"]`);
    const title = assignmentCard.querySelector('h2').textContent;
    const description = assignmentCard.querySelector('.assignment-description').textContent;
    const className = assignmentCard.querySelector('.class-badge').textContent;

    // Fill the form with current values
    document.getElementById('modalTitleInput').value = title;
    document.getElementById('modalDescriptionInput').value = description;

    // Set the class select to match current class
    const classSelect = document.getElementById('modalClassId');
    for (let option of classSelect.options) {
        if (option.text === className) {
            option.selected = true;
            break;
        }
    }

    // Set current due date (you'll need to add a data attribute to the assignment card with the due date)
    const dueDateStr = assignmentCard.querySelector('.due-date').getAttribute('data-due-date');
    document.getElementById('modalDueDateInput').value = dueDateStr;
}

// Close assignment modal
function closeAssignmentModal() {
    document.getElementById('assignmentModal').style.display = 'none';
}

// Handle updating assignment
document.getElementById('updateAssignmentForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const updatedData = {
        class_id: document.getElementById('modalClassId').value,
        title: document.getElementById('modalTitleInput').value,
        description: document.getElementById('modalDescriptionInput').value,
        due_date: document.getElementById('modalDueDateInput').value
    };

    fetch(`/update_assignment/${currentAssignmentId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeAssignmentModal();
            location.reload();
        } else {
            alert('Error updating assignment: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating assignment');
    });
});

// Delete assignment
function deleteAssignment() {
    if (confirm('Are you sure you want to delete this assignment? This action cannot be undone.')) {
        fetch(`/delete_assignment/${currentAssignmentId}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                closeAssignmentModal();
                location.reload();
            } else {
                alert('Error deleting assignment: ' + data.error);
            }
        })
        .catch(error => {
            alert('Error deleting assignment');
            console.error('Error:', error);
        });
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Set minimum date for due_date inputs to current date
    const dueDateInputs = document.querySelectorAll('input[type="datetime-local"]');
    dueDateInputs.forEach(input => {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        input.min = now.toISOString().slice(0, 16);
    });
});