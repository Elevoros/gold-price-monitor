import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from pushover_complete import PushoverAPI

# Ρυθμίσεις Pushover - Τα κλειδιά λαμβάνονται από τα GitHub Secrets
PUSHOVER_USER_KEY = os.getenv('PUSHOVER_USER_KEY')
PUSHOVER_API_TOKEN = os.getenv('PUSHOVER_API_TOKEN')

# URL της ιστοσελίδας (παράδειγμα: BullionByPost)
URL = 'https://www.bullionbypost.co.uk/gold-coins/full-sovereign-gold-coin/bullion-gold-sovereign/'

def get_current_price():
    """Παίρνει την τρέχουσα τιμή της χρυσής λίρας από την ιστοσελίδα."""
    try:
        # Ρυθμίσεις για να τρέχει το Chrome στο παρασκήνιο (headless)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Χρήση του webdriver-manager για να κατεβάσει αυτόματα τον driver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(URL)
        time.sleep(5)
        price_element = driver.find_element(By.XPATH, '//*[@id="productPage"]/div[2]/div/div[2]/div[1]/div[1]/span/span[2]')
        price_text = price_element.text
        current_price = float(price_text.replace('£', '').replace(',', ''))
        print(f"Τρέχουσα τιμή: {current_price} GBP")
        return current_price
    except Exception as e:
        print(f"Σφάλμα κατά τη λήψη της τιμής: {e}")
        return None
    finally:
        if 'driver' in locals():
            driver.quit()

def send_notification(message):
    """Στέλνει ειδοποίηση στο κινητό μέσω του Pushover."""
    try:
        pushover_api = PushoverAPI(PUSHOVER_API_TOKEN)
        pushover_api.send_message(PUSHOVER_USER_KEY, message, title="Ειδοποίηση Τιμής Χρυσής Λίρας")
        print("Ειδοποίηση στάλθηκε επιτυχώς!")
    except Exception as e:
        print(f"Σφάλμα κατά την αποστολή ειδοποίησης: {e}")

if __name__ == "__main__":
    print("Το bot ξεκίνησε. Ελέγχει την τιμή της χρυσής λίρας.")
    current_price = get_current_price()
    if current_price is not None:
        message = f"Τρέχουσα τιμή χρυσής λίρας: £{current_price}"
        send_notification(message)
    else:
        send_notification("Σφάλμα: Δεν είναι δυνατή η λήψη της τιμής της χρυσής λίρας.")
