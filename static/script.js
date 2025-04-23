document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const textarea = document.getElementById("text");

    // Handle form validation and submission feedback
    if (form && textarea) {
        form.addEventListener("submit", function (e) {
            const text = textarea.value.trim();
            if (!text) {
                alert("Please write something before submitting!");
                e.preventDefault();
            } else {
                const submitBtn = form.querySelector("button[type='submit']");
                submitBtn.disabled = true;
                submitBtn.innerHTML = `<i class="fa fa-spinner fa-spin"></i> Submitting...`;
            }
        });

        // Add a live character counter
        const counter = document.createElement("div");
        counter.style.textAlign = "right";
        counter.style.fontSize = "0.9rem";
        counter.style.color = "#666";
        textarea.parentElement.appendChild(counter);

        textarea.addEventListener("input", () => {
            counter.textContent = `${textarea.value.length} characters`;
        });

        // Highlight textarea on focus
        textarea.addEventListener("focus", () => {
            textarea.style.boxShadow = "0 0 5px rgba(33, 150, 243, 0.6)";
        });

        // Remove highlight on blur
        textarea.addEventListener("blur", () => {
            textarea.style.boxShadow = "none";
        });
    }

    // Display current date
    const dateEl = document.getElementById("current-date");
    if (dateEl) {
        const today = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        dateEl.textContent = today.toLocaleDateString(undefined, options);
    }

    // Load weather using geolocation
    const weatherEl = document.getElementById("weather");
    if (weatherEl && navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(success, error);
    }

    function success(position) {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        fetchWeather(lat, lon);
    }

    function error() {
        weatherEl.textContent = "Location permission denied.";
    }

    function fetchWeather(lat, lon) {
        const apiKey = "3f6c46067682a1ee8001fc84f0b7755b";
        const url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&units=metric&appid=${apiKey}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                const temp = data.main.temp;
                const city = data.name;
                const description = data.weather[0].description;
                weatherEl.textContent = `${city}: ${description}, ${temp}°C`;
            })
            .catch(() => {
                weatherEl.textContent = "Unable to fetch weather.";
            });
    }
});