import os, socket, subprocess, sys, time, unittest
from contextlib import suppress
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5001")
PORT     = int(os.getenv("TEST_PORT", "5001"))
TEST_USER = {"username": "testuser", "password": "123456"}

LOGIN_USERNAME_INP = "#username"
LOGIN_PASSWORD_INP = "#password"
LOGIN_SUBMIT_BTN   = "input[type='submit'], button[type='submit']"

CTA_DASHBOARD      = "a.btn-success[href='/data/create_diary']"
TITLE_SELECTOR     = "#diaryTitle"
CONTENT_SELECTOR   = "#diaryContent"
SAVE_BTN_SELECTOR  = "button[type='submit'], i.bi-check-lg"
FAB_BTN            = ".fab-btn"
CARD_TITLE_SELECTOR= ".card-title"

def wait_port(host, port, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        with suppress(OSError):
            with socket.create_connection((host, port), 1):
                return
        time.sleep(0.5)
    raise RuntimeError("Flask server didn’t start")

class MoodDiaryE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = subprocess.Popen([sys.executable, "run.py"])
        wait_port("127.0.0.1", PORT)

        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1400,900")
        opts.add_argument("--disable-gpu")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])

        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=opts,
        )

    @classmethod
    def tearDownClass(cls):
        with suppress(Exception): cls.driver.quit()
        with suppress(Exception):
            cls.server.terminate(); cls.server.wait(timeout=5)

    # ─ helpers ─
    def wait(self, cond, timeout=12):
        return WebDriverWait(self.driver, timeout).until(cond)

    def login(self):
        """UI-логин + переход сразу на /home."""
        self.driver.delete_all_cookies()
        with suppress(Exception):
            self.driver.get(f"{BASE_URL}/auth/logout")

        self.driver.get(f"{BASE_URL}/auth/login")
        self.wait(EC.presence_of_element_located((By.CSS_SELECTOR, LOGIN_USERNAME_INP))
                  ).send_keys(TEST_USER["username"])
        self.driver.find_element(By.CSS_SELECTOR, LOGIN_PASSWORD_INP
                  ).send_keys(TEST_USER["password"])
        self.driver.find_element(By.CSS_SELECTOR, LOGIN_SUBMIT_BTN).click()

        # ждём исчезновения SweetAlert
        self.wait(lambda d: not d.find_elements(By.CSS_SELECTOR, ".swal2-container"))
        # переходим в кабинет
        self.driver.get(f"{BASE_URL}/home")

    def open_create_diary(self):
        """CTA на пустом дашборде или FAB, если записи уже есть."""
        try:
            self.wait(EC.element_to_be_clickable((By.CSS_SELECTOR, CTA_DASHBOARD)),
                      timeout=4).click()
        except Exception:
            self.wait(EC.element_to_be_clickable((By.CSS_SELECTOR, FAB_BTN))).click()

    # ─ tests ─
    def test_homepage_smoke(self):
        self.driver.get(BASE_URL)
        h1 = self.wait(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        self.assertRegex(h1.text, r"(Mood|Track)",
                         "Главный заголовок не найден")

    def test_login_and_logout_flow(self):
        self.login()
        # Log Out
        self.wait(EC.element_to_be_clickable((By.LINK_TEXT, "Log Out"))).click()
        # ждём, когда появится линк Log In (редирект на /index)
        self.wait(EC.visibility_of_element_located((By.LINK_TEXT, "Log In")))

    def test_create_diary_card(self):
        self.login()
        self.open_create_diary()

        title = f"UI-entry {int(time.time())}"
        self.wait(EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_SELECTOR))
                  ).send_keys(title)
        self.driver.find_element(By.CSS_SELECTOR, CONTENT_SELECTOR).send_keys(
            "Automated UI-test plain text.")
        self.driver.find_element(By.CSS_SELECTOR, SAVE_BTN_SELECTOR).click()

        self.wait(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, CARD_TITLE_SELECTOR)))
        titles = [t.text.strip() for t
                  in self.driver.find_elements(By.CSS_SELECTOR, CARD_TITLE_SELECTOR)]
        self.assertIn(title, titles, "Карточка не появилась")

if __name__ == "__main__":
    unittest.main(verbosity=2)