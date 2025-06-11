function updateDateTime() {
    const now = new Date();
    const options = {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    };
    const dateTimeString = now.toLocaleString('en-US', options).replace(',', '');
    document.getElementById('current-datetime').textContent = dateTimeString;
}

// Initialize and update every second
updateDateTime();
setInterval(updateDateTime, 1000);