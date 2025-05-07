// This file contains the JavaScript code for the diary application
// Function to handle the form submission
document.querySelector('.new-diary-btn').addEventListener('click', () => {
    document.getElementById('uploadModal').style.display = 'block';
});
document.getElementById('closeModal').addEventListener('click', () => {
    document.getElementById('uploadModal').style.display = 'none';
});



document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('diaryGrid');
    const cards = Array.from(container.querySelectorAll('.diary-card'));

    // based on the datetime attribute of the <time> element
    cards.sort((a, b) => {
        const timeA = new Date(a.querySelector('time').getAttribute('datetime'));
        const timeB = new Date(b.querySelector('time').getAttribute('datetime'));
        return timeB - timeA;
    });

    // Clear the container and append sorted cards
    container.innerHTML = '';
    cards.forEach(card => container.appendChild(card));
});