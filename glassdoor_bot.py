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

def glassdoor_login(driver):
    log.info("Attempting Glassdoor Login...")
    driver.get("https://www.glassdoor.co.in/profile/login_input.htm")
    
    print("\n" + "="*60)
    print("🤖 [ACTION REQUIRED] 🤖")
    print("Please login manually to GLASSDOOR in the Chrome window.")
    print("If it asks for OTP or Captcha, please complete it.")
    input("👉 Press ENTER here in the terminal when you are fully logged in... ")
    print("="*60 + "\n")
    
    log.info("✅ Proceeding to Glassdoor Job Search...")

def search_jobs(driver, keyword):
    log.info(f"Searching for {keyword} on Glassdoor...")
    # Basic search structure for Glassdoor India (locId=115 for India) 
    # fromAge=7 limits to last 7 days
    url = f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={keyword.replace(' ', '%20')}&locT=N&locId=115&locKeyword=India&fromAge=7"
    
    if config.SEARCH['remote_only']:
        url += "&remoteWorkType=1"
        
    driver.get(url)
    time.sleep(5)

def apply_to_job(driver, job_card, applied_titles):
    try:
        # Click the job card to load right pane
        job_card.click()
        time.sleep(random.uniform(2, 4))
        
        wait = WebDriverWait(driver, 10)
        
        try:
            # We look for the job title in the primary header (broadened selectors)
            title_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1, h2, .JobDetails_jobTitle__Rw_gn, [data-test='job-title']")))
            job_title = title_el.text.strip()
        except:
            job_title = "Unknown Glassdoor Role"
            
        if job_title in applied_titles:
            log.info(f"⏭️ Already applied: {job_title}")
            return False
            
        log.info(f"📋 Job: {job_title}")
        
        # Find Easy Apply button specifically, or any Apply button
        try:
            # Look for button that says "Easy Apply" or "Apply Now"
            apply_btn = driver.find_element(By.XPATH, "//button[contains(., 'Easy Apply') or contains(., 'Apply Now') or contains(@class, 'EasyApplyButton')]")
            apply_btn.click()
            time.sleep(3)
            
            # Form processing logic (Glassdoor forms often use modals)
            log.info("Opened Glassdoor Easy Apply Modal.")
            
            steps = 0
            while steps < 8:
                time.sleep(2)
                try:
                    # Look for Submit
                    submit_btn = driver.find_element(By.XPATH, "//button[span[contains(text(), 'Submit')]]")
                    submit_btn.click()
                    time.sleep(3)
                    log.info(f"✅ APPLIED (Glassdoor): {job_title}")
                    applied_titles.add(job_title)
                    return True
                except:
                    pass
                    
                try:
                    # Look for Continue
                    continue_btn = driver.find_element(By.XPATH, "//button[span[contains(text(), 'Continue')]]")
                    continue_btn.click()
                except:
                    try:
                        # Close if stuck
                        close_btn = driver.find_element(By.CSS_SELECTOR, "button.CloseButton")
                        close_btn.click()
                        time.sleep(1)
                        # Confirm close
                        confirm_close = driver.find_element(By.XPATH, "//button[span[contains(text(), 'Discard')]]")
                        confirm_close.click()
                        log.warning("Exiting Glassdoor Apply due to complex form.")
                        break
                    except:
                        pass
                steps += 1
                
            return False
            
        except Exception:
            log.info(f"⏭️ Not a Glassdoor Easy Apply or button not found: {job_title}")
            return False
            
    except Exception as e:
        log.error(f"Error on Glassdoor job card: {e}")
        return False

def run_glassdoor_bot():
    log.info("--- GLASSDOOR BOT STARTED ---")
    driver = get_driver()
    applied_titles = set()
    total_applied = 0
    
    try:
        glassdoor_login(driver)
        for keyword in config.SEARCH["keywords"]:
            search_jobs(driver, keyword)
            
            page_clicks = 0
            while True:
                try:
                    # Glassdoor job cards (Broadened to typical list items if data-test fails)
                    cards = driver.find_elements(By.CSS_SELECTOR, "li[data-test='jobListing'], .JobCard_jobCardContainer___K1Zn, div[data-test='job-list'] li")
                    log.info(f"Found {len(cards)} jobs on Glassdoor (Page {page_clicks + 1}).")
                    
                    if not cards:
                        log.info("No job cards found. Moving to next keyword.")
                        break
                    
                    for card in cards:
                        if apply_to_job(driver, card, applied_titles):
                            total_applied += 1
                            time.sleep(random.uniform(1.5, 3.0))
                            
                    # Find and click Next button
                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, "button[data-test='pagination-next']")
                        if not next_btn.is_enabled() or "disabled" in next_btn.get_attribute("class"):
                            log.info("Reached end of pagination for this keyword.")
                            break
                        next_btn.click()
                        time.sleep(random.uniform(3, 5))
                        page_clicks += 1
                    except Exception:
                        log.info("Reached end of pagination for this keyword.")
                        break
                        
                except Exception as e:
                    log.error(f"Failed to process Glassdoor cards: {e}")
                    break
            
    except Exception as e:
        log.error(f"Glassdoor Bot Error: {e}")
    finally:
        log.info(f"Glassdoor Session Completed. Total Applied: {total_applied}")
        driver.quit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_glassdoor_bot()
