from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import datetime
import os
import time
import re
import requests
import tempfile  # <-- πρόσθετο

# Telegram config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram token ή chat ID δεν έχουν ρυθμιστεί.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Μήνυμα στο Telegram στάλθηκε με επιτυχία.")
    except Exception as e:
        print(f"Σφάλμα στην αποστολή Telegram: {e}")

def get_latest_bulletin_url_selenium():
    options = Options()
    # Αφαίρεσε το headless για να φαίνεται το παράθυρο
    # options.add_argument("--headless")

    # Βάλε ρεαλιστικό User-Agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    # Προσθήκη προσωρινού user-data-dir για αποφυγή conflicts
    temp_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_dir}")

    # Προαιρετικά: options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.bankofgreece.gr/en/main-tasks/markets/gold/gold-price-bulletin")

    # Άσε τη σελίδα να φορτώσει (5 δευτερόλεπτα)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Ψάξε για links με pattern που δείχνουν σε δελτία τιμών (πχ PDF με 'bulletin')
    links = soup.find_all('a', href=True)
    for link in links:
        href = link['href']
        if re.search(r'bulletin', href, re.IGNORECASE) and href.lower().endswith('.pdf'):
            full_url = href if href.startswith('http') else "https://www.bankofgreece.gr" + href
            return full_url

    print("Δεν βρέθηκε σύνδεσμος δελτίου τιμών.")
    return None

if __name__ == "__main__":
    print("Ξεκινάει η αναζήτηση του πιο πρόσφατου δελτίου τιμών...")
    latest_bulletin_url = get_latest_bulletin_url_selenium()

    if latest_bulletin_url:
        print(f"Πιο πρόσφατο δελτίο: {latest_bulletin_url}")

        message = (
            f"*Ενημέρωση Τιμών Χρυσής Λίρας - {datetime.date.today().strftime('%d/%m/%Y')}*\n"
            f"Το πιο πρόσφατο δελτίο τιμών είναι διαθέσιμο εδώ:\n"
            f"{latest_bulletin_url}\n"
            f"\n(Αυτές είναι οι επίσημες τιμές από την Τράπεζα της Ελλάδος.)"
        )

        send_telegram_message(message)
    else:
        print("Δεν βρέθηκε δελτίο τιμών.")
