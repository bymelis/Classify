function openCreateClassModal() {
    document.getElementById('createClassModal').style.display = 'block';
}

function closeCreateClassModal() {
    document.getElementById('createClassModal').style.display = 'none';
}

function dismissMainFlash() {
    const flashMessage = document.getElementById('main-flash-message');
    if (flashMessage) {
        flashMessage.style.opacity = '0';
        setTimeout(() => {
            flashMessage.style.display = 'none';
        }, 300);
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

window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
}