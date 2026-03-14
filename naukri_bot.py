import logging
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

import config

log = logging.getLogger(__name__)

def get_driver():
    import os
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
    return driver

def naukri_login(driver):
    log.info("Attempting Naukri Login...")
    driver.get("https://login.naukri.com/nLogin/Login.php")
    
    print("\n" + "="*60)
    print("🤖 [ACTION REQUIRED] 🤖")
    print("Please login manually in the Chrome window if you aren't already.")
    print("If it asks for OTP or Captcha, please complete it.")
    input("👉 Press ENTER here in the terminal when you are fully logged in... ")
    print("="*60 + "\n")
    
    log.info("✅ Proceeding to job hunt...")

def search_jobs(driver, keyword):
    log.info(f"Searching for {keyword} on Naukri...")
    
    # Refined Naukri URL structure for Remote specifically
    if config.SEARCH['remote_only']:
        url = f"https://www.naukri.com/remote-{keyword.replace(' ', '-')}-jobs-in-{config.SEARCH['location'].replace(' ', '-')}"
        url += "?jobAge=7"
    else:
        url = f"https://www.naukri.com/{keyword.replace(' ', '-')}-jobs-in-{config.SEARCH['location'].replace(' ', '-')}"
        url += "?jobAge=7"
        
    driver.get(url)
    time.sleep(5)

# ─── Smart Answer Engine ──────────────────────────────────────
def find_answer(question_text):
    q = question_text.lower().strip()
    for keyword, answer in config.SAVED_ANSWERS.items():
        if keyword.lower() in q:
            return str(answer)

    # Default fallbacks
    if any(w in q for w in ["year", "experience", "how long", "how many"]):
        return "5"
    if any(w in q for w in ["salary", "ctc", "compensation", "pay"]):
        return "800000"
    if any(w in q for w in ["notice", "join", "start", "available"]):
        return "Immediately"
    if any(w in q for w in ["yes", "no", "are you", "do you", "have you", "can you"]):
        return "Yes"

    log.warning(f"⚠️  Unknown Naukri question: {question_text[:60]}... → defaulting to 'Yes'")
    return "Yes"

def human_type(element, text):
    for char in str(text):
        try:
            element.send_keys(char)
            time.sleep(random.uniform(0.01, 0.05))
        except: pass

def fill_field(field, answer):
    try:
        tag = field.tag_name.lower()
        field_type = field.get_attribute("type") or ""

        if tag == "select":
            sel = Select(field)
            try:
                sel.select_by_visible_text(answer)
            except Exception:
                for opt in sel.options:
                    if answer.lower() in opt.text.lower():
                        sel.select_by_visible_text(opt.text)
                        break

        elif field_type in ["radio", "checkbox"]:
            if not field.is_selected():
                try: field.click()
                except: 
                    try:
                        parent_label = field.find_element(By.XPATH, "./following-sibling::label | ./parent::label")
                        parent_label.click()
                    except: pass

        elif tag in ["input", "textarea"]:
            if field_type not in ["file", "submit", "button", "hidden"]:
                val = field.get_attribute("value")
                if not val:
                    field.clear()
                    human_type(field, answer)

    except Exception: pass

def apply_to_job(driver, job_card, applied_titles):
    try:
        # Get Job Title
        try:
            title_el = job_card.find_element(By.CSS_SELECTOR, "a.title")
            job_title = title_el.text.strip()
            job_url = title_el.get_attribute('href')
        except:
            job_title = "Unknown Naukri Role"
            job_url = None
            
        if job_title in applied_titles:
            log.info(f"⏭️ Already applied: {job_title}")
            return False
            
        log.info(f"📋 Job: {job_title}")
        
        if not job_url:
            return False
            
        # Naukri opens jobs in a new tab, so we click the link and switch
        driver.execute_script(f"window.open('{job_url}', '_blank');")
        time.sleep(2)
        
        # Switch to new tab
        driver.switch_to.window(driver.window_handles[-1])
        
        wait = WebDriverWait(driver, 10)
        
        # Find Apply Button
        try:
            apply_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.apply-message, #apply-button, .apply-button")))
            
            if "Already Applied" in apply_btn.text:
                log.info(f"⏭️ Already applied previously: {job_title}")
            else:
                apply_btn.click()
                time.sleep(3)
                
                # Handling Naukri's popup chat/form after clicking Apply
                try:
                    # check for inputs first
                    chat_inputs = driver.find_elements(By.XPATH, "//div[contains(@class, 'chatbot')]//input[not(@type='hidden')] | //div[contains(@id, 'chat')]//input[not(@type='hidden')] | //div[contains(@class, 'apply-form')]//input[not(@type='hidden')] | //div[contains(@class, 'apply-form')]//select")
                    for inp in chat_inputs:
                        try:
                            # Try finding nearest label/text
                            q_text = inp.find_element(By.XPATH, "./parent::div/preceding-sibling::div[contains(@class, 'botMsg')] | ./preceding::label[1] | ./parent::div/label").text
                        except:
                            q_text = "Naukri side input"
                        fill_field(inp, find_answer(q_text))
                        time.sleep(1)
                        
                    chat_submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Update and Apply') or contains(text(), 'Save and Apply') or contains(text(), 'Send')]")
                    chat_submit_btn.click()
                    time.sleep(2)
                    log.info("Handled Naukri side-panel form.")
                except:
                    pass
                
                log.info(f"✅ APPLIED (Naukri): {job_title}")
                applied_titles.add(job_title)
                
            # Close tab and switch back
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return True
            
        except Exception:
            log.info(f"⏭️ Apply button not found or it redirected externally: {job_title}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return False
            
    except Exception as e:
        log.error(f"Error on Naukri job card: {e}")
        # Make sure we close extra tabs if stuck
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        return False

def run_naukri_bot():
    log.info("--- NAUKRI BOT STARTED ---")
    driver = get_driver()
    applied_titles = set()
    total_applied = 0
    max_apps = config.SEARCH["max_applications"]
    
    try:
        naukri_login(driver)
        for keyword in config.SEARCH["keywords"]:
            search_jobs(driver, keyword)
            
            page_clicks = 0
            while True:
                try:
                    # Scroll to load jobs
                    for _ in range(3):
                        driver.execute_script("window.scrollBy(0, 1000)")
                        time.sleep(1)
                        
                    cards = driver.find_elements(By.CSS_SELECTOR, ".srp-jobtuple-wrapper, .jobTuple")
                    log.info(f"Found {len(cards)} jobs on Naukri (Page/View {page_clicks + 1}).")
                    
                    if not cards:
                        log.info("No job cards found. Moving to next keyword.")
                        break
                    
                    for card in cards:
                        if apply_to_job(driver, card, applied_titles):
                            total_applied += 1
                            time.sleep(1.5)
                            
                    # Attempt to find "Next Page" button
                    try:
                        next_btn = driver.find_element(By.XPATH, "//a[contains(@class, 'next') or contains(text(), 'Next')]")
                        next_btn.click()
                        time.sleep(3)
                        page_clicks += 1
                    except Exception:
                        log.info("Reached end of pagination for this keyword.")
                        break
                            
                except Exception as e:
                    log.error(f"Failed to process Naukri cards: {e}")
                    break
            
    except Exception as e:
        log.error(f"Naukri Bot Error: {e}")
    finally:
        log.info(f"Naukri Session Completed. Total Applied: {total_applied}")
        driver.quit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_naukri_bot()
