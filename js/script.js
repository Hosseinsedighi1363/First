document.addEventListener('DOMContentLoaded', function() {
    // Quiz Timer
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        let timeInSeconds = 10 * 60; // 10 minutes

        const timerInterval = setInterval(() => {
            const minutes = Math.floor(timeInSeconds / 60);
            let seconds = timeInSeconds % 60;

            // Add leading zero to seconds if needed
            seconds = seconds < 10 ? '0' + seconds : seconds;

            timerElement.textContent = `${minutes}:${seconds}`;

            if (timeInSeconds <= 0) {
                clearInterval(timerInterval);
                alert('زمان آزمون به پایان رسید!');
                // Here you would typically auto-submit the form
                // window.location.href = 'results.html';
            }

            timeInSeconds--;
        }, 1000);
    }
});