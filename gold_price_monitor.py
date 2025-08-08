import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Επιστρέφει τον σύνδεσμο του πιο πρόσφατου δελτίου
def get_latest_bulletin_url_selenium():
    print("Ξεκινάει η αναζήτηση του πιο πρόσφατου δελτίου τιμών...")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # 🔧 Αποφυγή προβλήματος με --user-data-dir
    options.add_argument(f"--user-data-dir=/tmp/selenium_profile_{int(time.time())}")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://www.bankofgreece.gr/en/main-tasks/markets/gold/gold-price-bulletin")
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.find_all("a", href=True)

        for link in links:
            href = link["href"]
            if "gold-price-bulletin" in href and href.endswith(".pdf"):
                full_url = "https://www.bankofgreece.gr" + href
                print(f"Βρέθηκε δελτίο: {full_url}")
                return full_url
    finally:
        driver.quit()

    print("Δεν βρέθηκε δελτίο τιμών.")
    return None

# Αποθήκευση τοπικά
def download_bulletin(pdf_url, filename="latest_gold_price_bulletin.pdf"):
    print("Κατεβάζω το δελτίο...")
    response = requests.get(pdf_url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Το αρχείο αποθηκεύτηκε ως {filename}")
    else:
        print("Αποτυχία λήψης του αρχείου PDF.")

# -- Εκκίνηση προγράμματος --
if __name__ == "__main__":
    latest_bulletin_url = get_latest_bulletin_url_selenium()
    if latest_bulletin_url:
        download_bulletin(latest_bulletin_url)
