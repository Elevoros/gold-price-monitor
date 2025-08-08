import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Περιβάλλον μεταβλητές για ασφάλεια
PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.environ.get("PUSHOVER_API_TOKEN")

def get_latest_bulletin_url_selenium():
    print("📡 Ξεκινάει η αναζήτηση του πιο πρόσφατου δελτίου τιμών...")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-data-dir=/tmp/selenium_profile_{int(time.time())}")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://www.bankofgreece.gr/en/main-tasks/markets/gold/gold-price-bulletin")
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        pdf_links = soup.select("a[href$='.pdf']")

        for link in pdf_links:
            href = link["href"]
            text = link.get_text(strip=True).lower()
            if "gold" in href.lower() or "χρυσ" in text:
                full_url = "https://www.bankofgreece.gr" + href
                print(f"✅ Βρέθηκε δελτίο: {full_url}")
                return full_url
    finally:
        driver.quit()

    print("❌ Δεν βρέθηκε δελτίο τιμών.")
    return None

def send_push_notification(message):
    print("📲 Αποστολή ειδοποίησης...")
    data = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message
    }
    response = requests.post("https://api.pushover.net/1/messages.json", data=data)
    if response.status_code == 200:
        print("✅ Ειδοποίηση εστάλη με επιτυχία.")
    else:
        print("❌ Αποτυχία αποστολής:", response.text)

def main():
    url = get_latest_bulletin_url_selenium()
    if url:
        send_push_notification(f"🟡 ΝΕΟ ΔΕΛΤΙΟ ΤΙΜΩΝ ΧΡΥΣΗΣ ΛΙΡΑΣ:\n{url}")
    else:
        send_push_notification("⚠️ Δεν βρέθηκε νέο δελτίο τιμών.")

if __name__ == "__main__":
    main()
