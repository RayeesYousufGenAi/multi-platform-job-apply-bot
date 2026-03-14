import logging
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

import config

log = logging.getLogger(__name__)

def get_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # ── PERSISTENT PROFILE TO REMEMBER LOGINS AND FORMS ──
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    options.add_argument(f"user-data-dir={user_data_dir}")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver

def foundit_login(driver):
    log.info("Attempting Foundit Login...")
    driver.get("https://www.foundit.in/rio/login")
    
    print("\n" + "="*60)
    print("🤖 [ACTION REQUIRED] 🤖")
    print("Please login manually to FOUNDIT in the Chrome window.")
    print("If it asks for OTP or Captcha, please complete it.")
    input("👉 Press ENTER here in the terminal when you are fully logged in... ")
    print("="*60 + "\n")
    
    log.info("✅ Proceeding to Foundit Job Search...")

def search_jobs(driver, keyword):
    log.info(f"Searching for {keyword} on Foundit...")
    # Using the Foundit query structure
    # time=1 is for past week
    url = f"https://www.foundit.in/srp/results?query={keyword.replace(' ', '%20')}&locations={config.SEARCH['location'].replace(' ', '%20')}&time=1"
    
    if config.SEARCH['remote_only']:
        # Note: Foundit sometimes uses base filters for work from home
        url += "&workFromHome=true"
        
    driver.get(url)
    time.sleep(5)

def apply_to_job(driver, job_card, applied_titles):
    try:
        # Get Job Title directly from card
        try:
            title_el = job_card.find_element(By.CSS_SELECTOR, ".jobTitle, h3")
            job_title = title_el.text.strip()
        except:
            job_title = "Unknown Foundit Role"
            
        if job_title in applied_titles:
            log.info(f"⏭️ Already applied: {job_title}")
            return False
            
        log.info(f"📋 Job: {job_title}")
        
        # Foundit usually has 'Apply' directly on the card or opens a new tab.
        try:
            apply_btn = job_card.find_element(By.XPATH, ".//button[contains(text(), 'Apply')] | .//div[contains(@class, 'applyBtn')]")
            if "Applied" in apply_btn.text:
                 log.info(f"⏭️ Already applied previously: {job_title}")
                 return False
                 
            apply_btn.click()
            time.sleep(3)
            
            # Check for direct success toast or form
            log.info(f"✅ APPLIED (Foundit): {job_title}")
            applied_titles.add(job_title)
            return True
        except Exception:
            log.info(f"⏭️ Apply button not straightforward: {job_title}")
            return False
            
    except Exception as e:
        log.error(f"Error on Foundit job card: {e}")
        return False

def run_foundit_bot():
    log.info("--- FOUNDIT BOT STARTED ---")
    driver = get_driver()
    applied_titles = set()
    total_applied = 0
    
    try:
        foundit_login(driver)
        for keyword in config.SEARCH["keywords"]:
            search_jobs(driver, keyword)
            
            page_clicks = 0
            while True:
                try:
                    # Scroll to load
                    for _ in range(4):
                        driver.execute_script("window.scrollBy(0, 800)")
                        time.sleep(1)
                        
                    cards = driver.find_elements(By.CSS_SELECTOR, ".srpResultCard, .job-tuple")
                    log.info(f"Found {len(cards)} jobs on Foundit (Page {page_clicks + 1}).")
                    
                    if not cards:
                        log.info("No job cards found. Moving to next keyword.")
                        break
                    
                    for card in cards:
                        if apply_to_job(driver, card, applied_titles):
                            total_applied += 1
                            time.sleep(random.uniform(1.0, 2.5))
                            
                    # Attempt pagination
                    try:
                        next_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'next')] | //button[contains(text(), 'Next')]")
                        if "disabled" in next_btn.get_attribute("class"):
                            log.info("Reached end of pagination for this keyword.")
                            break
                            
                        # Scroll to next button sometimes needed
                        driver.execute_script("arguments[0].scrollIntoView();", next_btn)
                        time.sleep(1)
                        next_btn.click()
                        time.sleep(4)
                        page_clicks += 1
                    except Exception:
                        log.info("Reached end of pagination for this keyword.")
                        break
                            
                except Exception as e:
                    log.error(f"Failed to process Foundit cards: {e}")
                    break
            
    except Exception as e:
        log.error(f"Foundit Bot Error: {e}")
    finally:
        log.info(f"Foundit Session Completed. Total Applied: {total_applied}")
        driver.quit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_foundit_bot()
