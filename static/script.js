// 页面加载完成后运行
document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const textarea = document.getElementById("text");

    if (form && textarea) {
        // 提交验证
        form.addEventListener("submit", function (e) {
            const text = textarea.value.trim();
            if (!text) {
                alert("Please write something before submitting!");
                e.preventDefault();
            } else {
                const btn = form.querySelector("button[type='submit']");
                btn.disabled = true;
                btn.innerHTML = `<i class="fa fa-spinner fa-spin"></i> Submitting...`;
            }
        });

        // 字数统计
        const counter = document.createElement("div");
        counter.style.textAlign = "right";
        counter.style.fontSize = "0.9rem";
        counter.style.color = "#666";
        textarea.parentElement.appendChild(counter);

        textarea.addEventListener("input", () => {
            counter.textContent = `${textarea.value.length} characters`;
        });

        // 输入框高亮
        textarea.addEventListener("focus", () => {
            textarea.style.boxShadow = "0 0 5px rgba(33, 150, 243, 0.6)";
        });

        textarea.addEventListener("blur", () => {
            textarea.style.boxShadow = "none";
        });
    }

    // 显示当前日期
    const dateEl = document.getElementById("current-date");
    if (dateEl) {
        const today = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        dateEl.textContent = today.toLocaleDateString(undefined, options);
    }

    // 获取定位并加载天气
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
        document.getElementById("weather").textContent = "Location permission denied";
    }

    function fetchWeather(lat, lon) {
        const apiKey = "3f6c46067682a1ee8001fc84f0b7755b";
        const url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&units=metric&appid=${apiKey}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                const temp = data.main.temp;
                const city = data.name;
                const weather = data.weather[0].description;
                document.getElementById("weather").textContent = `${city}: ${weather}, ${temp}°C`;
            })
            .catch(err => {
                document.getElementById("weather").textContent = "Unable to fetch weather.";
            });
    }
});