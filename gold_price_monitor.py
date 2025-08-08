
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import os

def get_html_with_selenium(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return html

def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram credentials not found.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

def scrape_prices():
    BOG_PRICES_PAGE = 'https://www.bankofgreece.gr/en/main-tasks/markets/gold/gold-price-bulletin'
    html = get_html_with_selenium(BOG_PRICES_PAGE)
    soup = BeautifulSoup(html, 'html.parser')
    print(soup.prettify()[:1000])  # Εκτυπώνει τα πρώτα 1000 χαρακτήρες για έλεγχο

    bulletin_links = soup.find_all('a', href=True)
    for link in bulletin_links:
        if 'bulletin' in link['href'] and link['href'].endswith('.pdf'):
            bulletin_url = 'https://www.bankofgreece.gr' + link['href']
            return bulletin_url

    return None

def main():
    bulletin_url = scrape_prices()
    if bulletin_url:
        message = f"Τελευταίο δελτίο τιμών χρυσής λίρας: {bulletin_url}"
        print(message)
        send_telegram_message(message)
    else:
        print("Δεν βρέθηκε δελτίο τιμών.")

if __name__ == "__main__":
    main()
