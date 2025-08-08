# Import the necessary libraries for web scraping and API calls
import requests
from bs4 import BeautifulSoup
import re
import datetime
import os

# --- Telegram Bot configuration ---
# We now get the bot token and chat ID from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- Bank of Greece Web Scraping Configuration ---
# The base URL for the Bank of Greece website
BOG_BASE_URL = 'https://www.bankofgreece.gr'
# The specific page for the gold price bulletins
BOG_PRICES_PAGE = 'https://www.bankofgreece.gr/en/main-tasks/markets/gold/gold-price-bulletin'

# Headers to make the request appear as if it's coming from a browser
# This helps to avoid 403 Forbidden errors and cache issues.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}


def get_latest_bulletin_url():
    try:
        response = requests.get(BOG_PRICES_PAGE, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        print(soup.prettify()[:1000])

        # Αντικατέστησε με το σωστό pattern εφόσον χρειαστεί
        latest_link = soup.find('a', href=re.compile(r'\?bulletin='))

        if latest_link and latest_link.get('href'):
            href = latest_link['href']
            full_url = href if href.startswith('http') else f"{BOG_BASE_URL}{href}"
            return full_url
        else:
            print("Σφάλμα: Δεν βρέθηκε σύνδεσμος με παράμετρο bulletin.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Σφάλμα κατά την ανάκτηση της κύριας σελίδας: {e}")
        return None


def scrape_prices(url):
    """
    Ανακτά τις τιμές αγοράς και πώλησης από ένα συγκεκριμένο URL δελτίου.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        container = soup.find('div', class_='list_container')
        if not container:
            print("Σφάλμα: Δεν βρέθηκε το container με την τιμή.")
            return None

        prices_table = container.find('table')
        if not prices_table:
            print("Σφάλμα: Δεν βρέθηκε ο πίνακας τιμών.")
            return None

        rows = prices_table.find_all('tr')
        for row in rows:
            if 'ΛΙΡΑ ΑΓΓΛΙΑΣ' in row.get_text():
                cells = row.find_all('td')
                if len(cells) >= 3:
                    buy_price_text = cells[1].get_text(strip=True).replace(',', '.')
                    sell_price_text = cells[2].get_text(strip=True).replace(',', '.')

                    buy_price = float(buy_price_text)
                    sell_price = float(sell_price_text)

                    return {'buy': buy_price, 'sell': sell_price}

        print("Σφάλμα: Δεν βρέθηκαν οι τιμές για τη Λίρα Αγγλίας.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Σφάλμα κατά την ανάκτηση του δελτίου τιμών: {e}")
        return None
    except (ValueError, IndexError, AttributeError) as e:
        print(f"Σφάλμα κατά την επεξεργασία των τιμών: {e}")
        return None


def send_telegram_message(message):
    """
    Στέλνει ένα μήνυμα σε ένα bot του Telegram.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Σφάλμα: Δεν έχουν ρυθμιστεί το Bot Token ή το Chat ID του Telegram ως μεταβλητές περιβάλλοντος.")
        return

    telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(telegram_api_url, json=payload, timeout=5)
        response.raise_for_status()
        print("Το μήνυμα στάλθηκε με επιτυχία στο Telegram.")
    except requests.exceptions.RequestException as e:
        print(f"Σφάλμα κατά την αποστολή του μηνύματος στο Telegram: {e}")

if __name__ == '__main__':
    latest_url = get_latest_bulletin_url()

    if latest_url:
        print(f"Βρέθηκε το πιο πρόσφατο δελτίο: {latest_url}")

        prices = scrape_prices(latest_url)

        if prices:
            print("\nΤιμές Χρυσής Λίρας Αγγλίας:")
            print(f"Αγορά: {prices['buy']} €")
            print(f"Πώληση: {prices['sell']} €")

            message_text = (
                f"*Ενημέρωση Τιμών Χρυσής Λίρας - {datetime.date.today().strftime('%d/%m/%Y')}*\n"
                f"--------------------------------------------------\n"
                f"**Τιμή Αγοράς (ΤτΕ):** {prices['buy']} €\n"
                f"**Τιμή Πώλησης (ΤτΕ):** {prices['sell']} €\n"
                f"\nΑυτές είναι οι επίσημες τιμές της Τράπεζας της Ελλάδος."
            )

            send_telegram_message(message_text)

