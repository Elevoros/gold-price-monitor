import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()  # φόρτωση από .env

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'},
        timeout=10
    )
    r.raise_for_status()
    print("Telegram message sent.")

def scrape_gold_price_selenium():
    options = Options()
    options.add_argument("--headless=new")  # για νέα headless λειτουργία
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://www.bankofgreece.gr/en/main-tasks/markets/gold/gold-price-bulletin")
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    # Βρες την ημερομηνία δελτίου
    header = soup.find('h1') or soup.find('h2')
    date_text = header.get_text(strip=True) if header else 'Άγνωστη ημερομηνία'

    # Πίνακας τιμών
    rows = soup.select("table tr")
    price_info = {}
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all('td')]
        if any("sovereign" in c.lower() or "λίρα αγγλίας" in c.lower() for c in cols):
            if len(cols) >= 3:
                price_info['item'] = cols[0]
                price_info['buy'] = cols[1].replace(',', '.')
                price_info['sell'] = cols[2].replace(',', '.')
                break

    return date_text, price_info if price_info else None

if __name__ == "__main__":
    date_text, info = scrape_gold_price_selenium()
    if info:
        msg = (
            f"*Δελτίο Τιμών – {date_text}*\n"
            f"{info['item']}\nΑγορά: {info['buy']} €\nΠώληση: {info['sell']} €"
        )
    else:
        msg = "⚠️ Δελτίο τιμών βρέθηκε αλλά η 'Λίρα Αγγλίας' δεν βρέθηκε στον πίνακα."
    print(msg)
    send_telegram_message(msg)
