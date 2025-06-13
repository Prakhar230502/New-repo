from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import pyotp
import time
import subprocess
import generate_access_token
import otp_test
from urllib.parse import urlparse, parse_qs
import config


def wait_for_element(driver, by, identifier, max_retries=3, wait_time=10, description="element"):
    for attempt in range(max_retries):
        try:
            WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((by, identifier)))
            print(f"{description} found!")
            return True
        except TimeoutException:
            print(f"Attempt {attempt + 1}: {description} not found, retrying...")
    print(f"❌ {description} not found after {max_retries} retries.")
    return False

def wait_for_url_change(driver, old_url, max_retries=3, wait_time=10):
    for attempt in range(max_retries):
        try:
            WebDriverWait(driver, wait_time).until(EC.url_changes(old_url))
            print("New URL loaded!")
            return True
        except TimeoutException:
            print(f"Attempt {attempt + 1}: URL did not change, retrying...")
    print("❌ URL did not change after retries.")
    return False


def generate_automated_access_token(user_id):

    link = generate_access_token.print_url(user_id)

    # Chrome options
    options = Options()
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--window-size=1920x1080")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--incognito")
    # options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    driver = webdriver.Chrome(options=options)
    driver.get(link)

    if not wait_for_element(driver, By.ID, "userid", description="User ID field"):
        driver.quit(); return

    driver.find_element(By.ID, "userid").send_keys(user_id)

    secret = None
    while secret is None:
        if not wait_for_element(driver, By.ID, "password", description="Password field"):
            driver.quit(); return
        if not wait_for_element(driver, By.CLASS_NAME, "button-orange.wide", description="Login Button"):
            driver.quit(); return

        driver.find_element(By.ID, "password").send_keys(config.config_keys[user_id]["password"])
        driver.find_element(By.CLASS_NAME, "button-orange.wide").submit()

        if not wait_for_element(driver, By.ID, "userid", description="Token field (2FA)"):
            driver.quit(); return

        token = otp_test.run_parser(config.config_keys[user_id]["qr_link"])
        print(f"{user_id}: Token: {token}")

        old_url = None

        try:
            token_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "userid"))
            )
            old_url = driver.current_url
            token_field.send_keys(Keys.CONTROL + "a")   # Select all
            token_field.send_keys(Keys.BACKSPACE)       # Delete existing content
            token_field.send_keys(str(token))           # Send token
        except Exception as e:
            print("{user_id}: ❌ Could not send token to token field:", e)
            driver.save_screenshot("token_input_error.png")
            continue

        if not wait_for_url_change(driver, old_url):
            continue  # Retry the entire while loop

        final_url = driver.current_url
        parsed = urlparse(final_url)
        query_params = parse_qs(parsed.query)
        secret = query_params.get("request_token", [None])[0]

    print(f"{user_id}: Secret: {secret}")
    generate_access_token.generate_access_token(user_id, secret)
    driver.quit()