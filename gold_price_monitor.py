import requests
from bs4 import BeautifulSoup
import re
import datetime

# The base URL for the Bank of Greece gold prices page
BOG_BASE_URL = 'https://www.bankofgreece.gr'
BOG_PRICES_PAGE = f'{BOG_BASE_URL}/kiries-leitourgies/agores/xrysos/deltia-timwn-xrysoy/timh-xryshs-liras'

# Telegram Bot configuration
# REPLACE WITH YOUR OWN VALUES
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

def get_latest_bulletin_url():
    """
    Finds and returns the URL for the latest gold price bulletin.
    """
    try:
        # Fetch the main gold prices page
        response = requests.get(BOG_PRICES_PAGE)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the link to the latest bulletin. The link typically has the 'bulletin' parameter.
        latest_link = soup.find('a', href=re.compile(r'\?bulletin='))

        if latest_link and 'href' in latest_link.attrs:
            return f"{BOG_BASE_URL}{latest_link['href']}"
        else:
            print("Σφάλμα: Δεν βρέθηκε ο σύνδεσμος για το πιο πρόσφατο δελτίο τιμών.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Σφάλμα κατά την ανάκτηση της κύριας σελίδας: {e}")
        return None

def scrape_prices(url):
    """
    Scrapes the buy and sell prices from a specific bulletin URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the table containing the prices.
        # The table is inside a div with class 'list_container'.
        # This CSS selector may need updating if the site's design changes.
        prices_table = soup.find('div', class_='list_container').find('table')

        if not prices_table:
            print("Σφάλμα: Δεν βρέθηκε ο πίνακας τιμών.")
            return None

        # Find the row for the 'ΛΙΡΑ ΑΓΓΛΙΑΣ' (English Sovereign)
        rows = prices_table.find_all('tr')
        for row in rows:
            # Look for the text 'ΛΙΡΑ ΑΓΓΛΙΑΣ' in the row
            if 'ΛΙΡΑ ΑΓΓΛΙΑΣ' in row.get_text():
                cells = row.find_all('td')
                if len(cells) >= 3:
                    # Clean the price strings (remove spaces, commas, etc.)
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
    except (ValueError, IndexError) as e:
        print(f"Σφάλμα κατά την επεξεργασία των τιμών: {e}")
        return None

def send_telegram_message(message):
    """
    Sends a message to a Telegram bot.
    """
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID":
        print("Σφάλμα: Δεν έχει ρυθμιστεί το Bot Token ή το Chat ID του Telegram.")
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
    # Step 1: Get the URL of the latest bulletin
    latest_url = get_latest_bulletin_url()
    
    if latest_url:
        print(f"Βρέθηκε το πιο πρόσφατο δελτίο: {latest_url}")
        
        # Step 2: Scrape the prices from the latest bulletin
        prices = scrape_prices(latest_url)

        if prices:
            print("\nΤιμές Χρυσής Λίρας Αγγλίας:")
            print(f"Αγορά: {prices['buy']} €")
            print(f"Πώληση: {prices['sell']} €")

            # Step 3: Prepare and send the message to Telegram
            message_text = (
                f"*Ενημέρωση Τιμών Χρυσής Λίρας - {datetime.date.today().strftime('%d/%m/%Y')}*\n"
                f"--------------------------------------------------\n"
                f"**Τιμή Αγοράς (ΤτΕ):** {prices['buy']} €\n"
                f"**Τιμή Πώλησης (ΤτΕ):** {prices['sell']} €\n"
                f"\nΑυτές είναι οι επίσημες τιμές της Τράπεζας της Ελλάδος."
            )
            
            send_telegram_message(message_text)

