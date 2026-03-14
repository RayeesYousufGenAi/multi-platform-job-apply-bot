import logging
import time
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

def indeed_login(driver):
    log.info("Attempting Indeed Login...")
    driver.get("https://secure.indeed.com/auth")
    
    print("\n" + "="*60)
    print("🤖 [ACTION REQUIRED] 🤖")
    print("Please login manually in the Chrome window using Google, Apple, or Email.")
    print("If it asks for OTP or Captcha, please complete it.")
    input("👉 Press ENTER here in the terminal when you are fully logged in... ")
    print("="*60 + "\n")
    
    log.info("✅ Proceeding to Job Search...")

def search_jobs(driver, keyword):
    log.info(f"Searching for {keyword} on Indeed...")
    # Base URL for India
    url = f"https://in.indeed.com/jobs?q={keyword.replace(' ', '+')}&l={config.SEARCH['location'].replace(' ', '+')}&fromage=7"
    if config.SEARCH['remote_only']:
        url += "&sc=0kf%3Aattr%28DSQF7%29%3B" # Remote filter on Indeed
        
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

    log.warning(f"⚠️  Unknown question: {question_text[:60]}... → defaulting to 'Yes'")
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
    """
    Complete Indeed Easy Apply handler.
    Indeed India opens smartapply.indeed.com in a NEW TAB.
    The form is a regular webpage, NOT an iframe.
    We fill all inputs on each page, click Continue/Next, repeat until Submit.
    """
    original_window = driver.current_window_handle
    original_num_windows = len(driver.window_handles)
    
    try:
        # Click the job card to load the right pane
        job_card.click()
        time.sleep(2)
        
        wait = WebDriverWait(driver, 10)
        
        # Get Job Title
        try:
            title_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobsearch-JobInfoHeader-title")))
            job_title = title_el.text.strip()
        except:
            job_title = "Unknown Indeed Role"
            
        if job_title in applied_titles:
            log.info(f"⏭️ Already applied: {job_title}")
            return False
            
        log.info(f"📋 Job: {job_title}")
        
        # ── STEP 1: Click the Apply button ──
        try:
            apply_btn = driver.find_element(By.ID, "indeedApplyButton")
        except:
            try:
                apply_btn = driver.find_element(By.CSS_SELECTOR, "button.jobsearch-IndeedApplyButton-newDesign, button[id*='indeedApply'], .ia-IndeedApplyButton")
            except:
                log.info(f"⏭️ No Easy Apply button for: {job_title}")
                return False
        
        apply_btn.click()
        time.sleep(5)  # Give Indeed time to open the new tab/window
        
        # ── STEP 2: Detect WHERE the application form opened ──
        new_window_opened = len(driver.window_handles) > original_num_windows
        in_iframe = False
        on_smartapply_page = False
        
        if new_window_opened:
            # Switch to the NEW tab (smartapply.indeed.com)
            for w in driver.window_handles:
                if w != original_window:
                    driver.switch_to.window(w)
                    break
            time.sleep(3)
            on_smartapply_page = True
            log.info(f"📌 Switched to new tab: {driver.current_url}")
        else:
            # Check if the current URL changed to smartapply
            current_url = driver.current_url
            if "smartapply" in current_url or "indeed.com/m/apply" in current_url:
                on_smartapply_page = True
                log.info(f"📌 Navigated to smartapply in same tab: {current_url}")
            else:
                # Try iframe as last resort
                try:
                    iframe = wait.until(EC.presence_of_element_located((
                        By.CSS_SELECTOR, 
                        "iframe[title*='Indeed'], iframe[name*='indeedapply'], iframe[src*='indeedapply'], iframe[src*='smartapply']"
                    )))
                    driver.switch_to.frame(iframe)
                    in_iframe = True
                    on_smartapply_page = True
                    log.info("📌 Entered Indeed Apply iframe.")
                except:
                    log.warning(f"❌ Could not find application form for: {job_title}")
                    return False
        
        # ── STEP 3: Fill forms and navigate pages until Submit ──
        success = False
        for step in range(20):  # max 20 pages
            time.sleep(4)
            
            # Wait for page to be fully loaded
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except: pass
            time.sleep(1)
            
            log.info(f"  📄 Form page {step + 1}...")
            
            # 3a. Fill ALL visible input fields on this page
            try:
                # Find all input containers - use very broad selectors for smartapply pages
                all_inputs = driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']):not([type='submit']):not([type='button']), select, textarea")
                
                for inp in all_inputs:
                    try:
                        # Skip recaptcha, hidden, and invisible inputs
                        inp_name = (inp.get_attribute("name") or "").lower()
                        inp_id = (inp.get_attribute("id") or "").lower()
                        if "recaptcha" in inp_name or "recaptcha" in inp_id:
                            continue
                        if not inp.is_displayed():
                            continue
                        # Skip if already filled
                        if inp.tag_name.lower() in ["input", "textarea"]:
                            existing_val = inp.get_attribute("value")
                            if existing_val and len(existing_val.strip()) > 0:
                                continue
                        
                        # Find the closest label for this input
                        q_text = ""
                        try:
                            # Try aria-label first
                            q_text = inp.get_attribute("aria-label") or ""
                        except: pass
                        if not q_text:
                            try:
                                inp_id = inp.get_attribute("id") or ""
                                if inp_id:
                                    label = driver.find_element(By.CSS_SELECTOR, f"label[for='{inp_id}']")
                                    q_text = label.text
                            except: pass
                        if not q_text:
                            try:
                                # Walk up to parent and find any label/legend
                                parent = inp.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ia-') or contains(@class, 'css-')][1]")
                                q_text = parent.find_element(By.XPATH, ".//label | .//legend | .//span[contains(@class, 'label')]").text
                            except: pass
                        if not q_text:
                            try:
                                q_text = inp.get_attribute("placeholder") or inp.get_attribute("name") or "misc"
                            except: q_text = "misc"
                        
                        answer = find_answer(q_text)
                        fill_field(inp, answer)
                    except Exception:
                        pass
                
                # Handle radio buttons and checkboxes separately
                try:
                    radio_groups = driver.find_elements(By.CSS_SELECTOR, "fieldset, div[role='radiogroup'], div[role='group']")
                    for group in radio_groups:
                        try:
                            legend = group.find_element(By.XPATH, ".//legend | .//label[1] | .//span[1]").text
                            answer = find_answer(legend)
                            # Try to click the first radio/checkbox option
                            options = group.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
                            for opt in options:
                                try:
                                    opt_label = opt.find_element(By.XPATH, "./following-sibling::label | ./parent::label | ./ancestor::label").text
                                    if answer.lower() in opt_label.lower() or opt_label.lower() in answer.lower():
                                        if not opt.is_selected():
                                            try: opt.click()
                                            except:
                                                try: opt.find_element(By.XPATH, "./following-sibling::label | ./parent::label | ./ancestor::label").click()
                                                except: pass
                                        break
                                except: pass
                            else:
                                # If no matching option, click the first one  
                                if options and not options[0].is_selected():
                                    try: options[0].click()
                                    except:
                                        try: options[0].find_element(By.XPATH, "./following-sibling::label | ./parent::label | ./ancestor::label").click()
                                        except: pass
                        except: pass
                except: pass
                    
            except Exception as e:
                log.warning(f"  Input fill error: {e}")
            
            # 3b. Look for action buttons (Submit takes priority over Continue)
            time.sleep(1)
            
            # Scroll to the bottom of the page to make sure buttons are visible
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            except: pass
            
            # Find ALL possible clickable elements on the page
            all_buttons = driver.find_elements(By.CSS_SELECTOR, 
                "button, input[type='submit'], a[role='button'], a.ia-button, "
                "div[role='button'], span[role='button'], "
                "a[class*='continue'], a[class*='submit'], a[class*='next'], "
                "button[class*='continue'], button[class*='submit'], "
                "[data-testid*='continue'], [data-testid*='submit'], [data-testid*='next']"
            )
            
            submit_btn = None
            continue_btn = None
            
            for btn in all_buttons:
                try:
                    if not btn.is_displayed():
                        continue
                    btn_text = (btn.text or btn.get_attribute("value") or "").lower().strip()
                    btn_aria = (btn.get_attribute("aria-label") or "").lower()
                    btn_class = (btn.get_attribute("class") or "").lower()
                    btn_id = (btn.get_attribute("id") or "").lower()
                    combined = f"{btn_text} {btn_aria} {btn_class} {btn_id}"
                    
                    if any(word in combined for word in ["submit your application", "submit application", "submit"]):
                        submit_btn = btn
                        break  # Submit is highest priority
                    elif any(word in combined for word in ["continue", "next", "review your application", "review"]):
                        if not continue_btn:
                            continue_btn = btn
                except: pass
            
            # If still no button found, try a last-resort XPATH search
            if not submit_btn and not continue_btn:
                try:
                    # Use translate() for case-insensitive matching
                    possible = driver.find_elements(By.XPATH,
                        "//*[self::button or self::a or self::input[@type='submit'] or self::div[@role='button']]"
                        "[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue') "
                        "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit') "
                        "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next') "
                        "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]")
                    for p in possible:
                        try:
                            if not p.is_displayed(): continue
                            p_text = p.text.lower()
                            if "submit" in p_text or "apply" in p_text:
                                submit_btn = p; break
                            elif "continue" in p_text or "next" in p_text:
                                if not continue_btn: continue_btn = p
                        except: pass
                except: pass
            
            # Click Submit if found
            if submit_btn:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                    time.sleep(0.5)
                    submit_btn.click()
                    time.sleep(4)
                    log.info(f"✅ APPLIED (Indeed): {job_title}")
                    applied_titles.add(job_title)
                    success = True
                    break
                except Exception as e:
                    log.warning(f"  Submit click failed: {e}")
                    try:
                        driver.execute_script("arguments[0].click();", submit_btn)
                        time.sleep(4)
                        log.info(f"✅ APPLIED (Indeed via JS): {job_title}")
                        applied_titles.add(job_title)
                        success = True
                        break
                    except: pass
            
            # Click Continue if found
            elif continue_btn:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_btn)
                    time.sleep(0.5)
                    continue_btn.click()
                    log.info(f"  ➡️ Clicked Continue/Next (page {step + 1})")
                except Exception as e:
                    try:
                        driver.execute_script("arguments[0].click();", continue_btn)
                        log.info(f"  ➡️ Clicked Continue/Next via JS (page {step + 1})")
                    except:
                        log.warning(f"  Continue click failed on page {step + 1}")
                        break
            else:
                log.warning(f"  No Continue/Submit button found on page {step + 1}. Stopping.")
                break
        
        # ── STEP 4: Cleanup ──
        if in_iframe:
            try: driver.switch_to.default_content()
            except: pass
        
        # Close extra tab and go back to original
        if len(driver.window_handles) > original_num_windows:
            try:
                driver.close()
                driver.switch_to.window(original_window)
            except: pass
        elif new_window_opened:
            try: driver.switch_to.window(original_window)
            except: pass
                
        return success
            
    except Exception as e:
        log.error(f"Error on Indeed job card: {e}")
        # Cleanup: always go back to safe state
        try: driver.switch_to.default_content()
        except: pass
        try:
            if len(driver.window_handles) > original_num_windows:
                driver.close()
                driver.switch_to.window(original_window)
        except: pass
        return False

def run_indeed_bot():
    log.info("--- INDEED BOT STARTED ---")
    driver = get_driver()
    applied_titles = set()
    total_applied = 0
    max_apps = config.SEARCH["max_applications"]
    
    try:
        indeed_login(driver)
        for keyword in config.SEARCH["keywords"]:
            search_jobs(driver, keyword)
            
            page_clicks = 0
            while True:
                # Parse Job Cards
                try:
                    cards = driver.find_elements(By.CSS_SELECTOR, ".job_seen_beacon")
                    log.info(f"Found {len(cards)} jobs on Indeed (Page {page_clicks + 1}).")
                    
                    if not cards:
                        log.info("No job cards found. Moving to next keyword.")
                        break
                    
                    for card in cards:
                        if apply_to_job(driver, card, applied_titles):
                            total_applied += 1
                            time.sleep(1.5)
                            
                    # Attempt pagination
                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, "a[data-testid='pagination-page-next']")
                        next_btn.click()
                        time.sleep(4)
                        page_clicks += 1
                    except Exception:
                        log.info("Reached end of pagination for this keyword.")
                        break
                            
                except Exception as e:
                    log.error(f"Failed to process Indeed cards: {e}")
                    break
            
    except Exception as e:
        log.error(f"Indeed Bot Error: {e}")
    finally:
        log.info(f"Indeed Session Completed. Total Applied: {total_applied}")
        driver.quit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_indeed_bot()
