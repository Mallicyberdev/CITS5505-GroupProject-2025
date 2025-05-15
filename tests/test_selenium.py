# tests/test_selenium.py
import os
import socket
import subprocess
import sys
import time
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ───────────────────────────  настройки  ─────────────────────────── #
BASE_URL  = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5001")
PORT      = int(os.getenv("TEST_PORT", "5001"))
TEST_USER = {"username": "testuser", "password": "123456"}
# ──────────────────────────────────────────────────────────────────── #


def wait_port(host: str, port: int, timeout: int = 60):
    """Блокирует поток, пока host:port не начнёт принимать соединения."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), 1):
                return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"Server on {host}:{port} didn't start within {timeout}s")


class MoodDiaryE2E(unittest.TestCase):
    """Мини-набор end-to-end-тестов."""

    @classmethod
    def setUpClass(cls):
        # 1. поднимаем Flask-сервер
        cls.server = subprocess.Popen([sys.executable, "run.py"])
        wait_port("127.0.0.1", PORT)

        # 2. headless-Chrome
        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless=new")
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

    # ─────────────────────────── helpers ──────────────────────────── #
    def setUp(self):
        """Каждый тест начинается с чистых cookies."""
        self.driver.delete_all_cookies()

    def wait(self, condition, timeout=12):
        return WebDriverWait(self.driver, timeout).until(condition)

    def click_submit(self):
        """Безопасно нажать submit (input † или button †)."""
        self.wait(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            )
        ).click()

    def login(self, username=TEST_USER["username"], password=TEST_USER["password"]):
        """Быстрый вход в систему (со сбросом состояния)."""
        # гарантированно выйдем из предыдущего сеанса
        self.driver.get(f"{BASE_URL}/auth/logout")
        self.driver.get(f"{BASE_URL}/auth/login")

        self.wait(EC.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.click_submit()

    # ───────────────────────────── tests ──────────────────────────── #
    def test_homepage_smoke(self):
        """Домашняя страница открывается и содержит ожидаемый заголовок."""
        self.driver.get(BASE_URL)
        heading = self.wait(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        self.assertRegex(heading.text, r"Mood|Emotional")

    def test_login_and_logout_flow(self):
        """Корректный логин → Logout → снова видим Log In."""
        self.login()

        # ждём ссылку Logout, затем выходим
        self.wait(EC.element_to_be_clickable((By.LINK_TEXT, "Logout"))).click()
        self.wait(EC.visibility_of_element_located((By.LINK_TEXT, "Log In")))

    def test_create_diary_card(self):
        """Создание дневника выводит карточку на дашборде."""
        self.login()

        # переходим на /home (dashboard)
        self.driver.get(f"{BASE_URL}/home")

        # ждём кнопку-плюс (FAB)
        fab = self.wait(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "a.fab-btn, a.btn-success.fab-btn, a[href*='create_diary']",
                )
            )
        )
        fab.click()

        # форма создания
        self.wait(EC.presence_of_element_located((By.ID, "title")))
        self.driver.find_element(By.ID, "title").send_keys("Selenium diary")
        self.driver.find_element(By.ID, "content").send_keys("Content from e2e test")
        self.click_submit()

        # возвращаемся на dashboard и проверяем карточку
        self.driver.get(f"{BASE_URL}/home")
        card = self.wait(
            EC.visibility_of_element_located(
                (By.XPATH, "//h5[contains(text(), 'Selenium diary')]")
            )
        )
        self.assertTrue(card.is_displayed())


if __name__ == "__main__":
    unittest.main(verbosity=2)