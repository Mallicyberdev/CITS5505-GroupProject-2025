# tests/test_ui.py
import os
import socket
import subprocess
import time
import unittest
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# --------------------------------------------------------------- #
BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5001")
PORT     = int(os.getenv("TEST_PORT", "5001"))
TEST_USER = {"username": "testuser", "password": "123456"}
# --------------------------------------------------------------- #


def wait_port(host: str, port: int, timeout: int = 60) -> None:
    """Блокирует поток, пока host:port не начнёт принимать соединения."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), 1):
                return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"Server on {host}:{port} didn't start within {timeout}s")


class MoodDiaryUITest(unittest.TestCase):
    """Набор базовых end-to-end тестов (без CSRF, без регистрации)."""

    @classmethod
    def setUpClass(cls):
        # 1. стартуем Flask
        cls.server = subprocess.Popen([sys.executable, "run.py"])
        wait_port("127.0.0.1", PORT)

        # 2. инициализируем Chrome (headless)
        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless=new")      # Chrome ≥ 109
        opts.add_argument("--window-size=1280,800")
        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=opts,
        )

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        cls.server.terminate()
        try:
            cls.server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.server.kill()

    # ──────────────────────────────────────────────────────────── #
    def wait(self, condition, timeout=8):
        return WebDriverWait(self.driver, timeout).until(condition)

    # ──────────────────────────────────────────────────────────── #
    #                     TEST CASES
    # ──────────────────────────────────────────────────────────── #
    def test_homepage_loads(self):
        """Домашняя страница открывается и содержит ожидаемый заголовок."""
        self.driver.get(BASE_URL)
        heading = self.wait(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        self.assertRegex(heading.text, r"Mood|Emotional", "Unexpected heading")

    def test_login_wrong_password(self):
        """Неправильный пароль выдаёт сообщение об ошибке."""
        self.driver.get(f"{BASE_URL}/auth/login")
        self.driver.find_element(By.ID, "username").send_keys(TEST_USER["username"])
        self.driver.find_element(By.ID, "password").send_keys("wrongpass")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        alert = self.wait(EC.visibility_of_element_located((By.CLASS_NAME, "alert")))
        self.assertIn("Invalid", alert.text)

    def test_login_and_logout_flow(self):
        """Успешный логин и корректный логаут."""
        self.driver.get(f"{BASE_URL}/auth/login")
        self.driver.find_element(By.ID, "username").send_keys(TEST_USER["username"])
        self.driver.find_element(By.ID, "password").send_keys(TEST_USER["password"])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        logout_link = self.wait(EC.element_to_be_clickable((By.LINK_TEXT, "Logout")))
        self.assertTrue(logout_link.is_displayed())

        logout_link.click()
        self.wait(EC.visibility_of_element_located((By.LINK_TEXT, "Login")))

    def test_theme_toggle(self):
        """Переключатель темы изменяет атрибут data-bs-theme на <body>."""
        self.driver.get(BASE_URL)
        body = self.driver.find_element(By.TAG_NAME, "body")
        initial = body.get_attribute("data-bs-theme") or "light"

        self.driver.find_element(By.ID, "themeSwitch").click()

        self.wait(
            lambda d: d.find_element(By.TAG_NAME, "body")
                      .get_attribute("data-bs-theme") != initial
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)