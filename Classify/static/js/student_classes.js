function openJoinModal() {
    document.getElementById('joinModal').style.display = 'block';
}

function closeJoinModal() {
    document.getElementById('joinModal').style.display = 'none';
}

window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
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