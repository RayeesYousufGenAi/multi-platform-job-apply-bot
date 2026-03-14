"""
╔══════════════════════════════════════════════════════════════╗
║        LinkedIn Easy Apply Bot — Rayees Yousuf               ║
║        Selenium-based Job Application Automation             ║
╚══════════════════════════════════════════════════════════════╝

Requirements:
    pip install selenium webdriver-manager

Run:
    python job_bot.py
"""

import time
import random
import logging
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException,
    ElementNotInteractableException, StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import config  # apna config.py

# ─── Logging Setup ────────────────────────────────────────────
log_file = f"applications_{datetime.now().strftime('%Y%m%d_%H%M')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ─── Helper: Human-like delay ─────────────────────────────────
def sleep(min_s=1.0, max_s=3.0):
    time.sleep(random.uniform(min_s, max_s))


# ─── Helper: Type like a human ────────────────────────────────
def human_type(element, text):
    element.clear()
    for char in str(text):
        element.send_keys(char)
        time.sleep(random.uniform(0.03, 0.12))


# ─── Browser Setup ────────────────────────────────────────────
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

    # Bot detection bypass
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ─── LinkedIn Login ───────────────────────────────────────────
def linkedin_login(driver):
    log.info("LinkedIn pe login ho raha hai...")
    driver.get("https://www.linkedin.com/login")
    
    print("\n" + "="*60)
    print("🤖 [ACTION REQUIRED] 🤖")
    print("Please login manually in the Chrome window if you aren't already.")
    print("If it asks for OTP or Captcha, please complete it.")
    input("👉 Press ENTER here in the terminal when you are fully logged in... ")
    print("="*60 + "\n")
    
    log.info("✅ Proceeding with job application engine...")
    return True


# ─── Search Jobs ──────────────────────────────────────────────
def search_jobs(driver, keyword):
    log.info(f"🔍 Searching: {keyword}")

    url = (
        f"https://www.linkedin.com/jobs/search/?"
        f"keywords={keyword.replace(' ', '%20')}"
        f"&location={config.SEARCH['location'].replace(' ', '%20')}"
        f"&f_AL=true"    # Easy Apply filter
        f"&f_WT=2"       # Remote filter
        f"&f_TPR=r604800" # Past Week (7 Days)
        f"&sortBy=DD"    # Latest first
    )

    # Experience level filter
    exp_map = {
        "Entry Level": "1",
        "Associate": "2",
        "Mid-Senior Level": "3",
        "Director": "4",
    }
    exp_codes = [
        exp_map[e] for e in config.SEARCH["experience_level"] if e in exp_map
    ]
    if exp_codes:
        url += "&f_E=" + "%2C".join(exp_codes)

    driver.get(url)
    sleep(3, 5)


# ─── Get Job Cards ────────────────────────────────────────────
def get_job_cards(driver):
    try:
        wait = WebDriverWait(driver, 10)
        cards = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item")
        ))
        return cards
    except TimeoutException:
        log.warning("Job cards nahi mile.")
        return []


# ─── Smart Answer Engine ──────────────────────────────────────
def find_answer(question_text):
    """
    Question text ke keywords dekh ke config.SAVED_ANSWERS se answer dhundhta hai.
    """
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


# ─── Fill Form Fields ─────────────────────────────────────────
def fill_field(field, answer):
    tag = field.tag_name.lower()
    field_type = field.get_attribute("type") or ""

    try:
        if tag == "select":
            sel = Select(field)
            try:
                sel.select_by_visible_text(answer)
            except Exception:
                # Partial match try karo
                for opt in sel.options:
                    if answer.lower() in opt.text.lower():
                        sel.select_by_visible_text(opt.text)
                        break

        elif field_type in ["radio", "checkbox"]:
            if not field.is_selected():
                try:
                    # In LinkedIn, the input is often hidden and the label needs to be clicked
                    parent_label = field.find_element(By.XPATH, "./following-sibling::label")
                    parent_label.click()
                except Exception:
                    # Fallback to direct clicking
                    field.click()

        elif tag in ["input", "textarea"]:
            if field_type not in ["file", "submit", "button"]:
                field.clear()
                human_type(field, answer)

    except (ElementNotInteractableException, StaleElementReferenceException) as e:
        log.debug(f"Field fill error: {e}")


# ─── Handle Easy Apply Modal ──────────────────────────────────
def handle_easy_apply_modal(driver, job_title):
    """
    Easy Apply modal ke through step by step jaata hai.
    Returns True agar successfully apply kiya, False otherwise.
    """
    wait = WebDriverWait(driver, 10)
    max_steps = 10
    step = 0

    while step < max_steps:
        step += 1
        sleep(1.5, 3)

        # ── Resume Upload Check ────────────────────────────
        try:
            upload = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            resume_path = Path(config.PERSONAL["resume_path"]).resolve()
            if resume_path.exists():
                upload.send_keys(str(resume_path))
                sleep(2)
                log.info("📄 Resume uploaded")
            else:
                log.warning(f"Resume file nahi mila: {resume_path}")
        except NoSuchElementException:
            pass

        # ── Fill All Visible Fields ────────────────────────
        try:
            questions = driver.find_elements(
                By.CSS_SELECTOR,
                ".jobs-easy-apply-form-section__grouping, "
                ".fb-form-element, "
                ".jobs-easy-apply-form-element"
            )

            for q_block in questions:
                try:
                    # Question text nikalo
                    label_el = None
                    for sel in ["label", ".fb-dash-form-element__label", ".t-bold", "span"]:
                        try:
                            label_el = q_block.find_element(By.CSS_SELECTOR, sel)
                            break
                        except Exception:
                            pass

                    q_text = label_el.text if label_el else ""
                    answer = find_answer(q_text)

                    # Fields fill karo
                    fields = q_block.find_elements(
                        By.CSS_SELECTOR,
                        "input, select, textarea"
                    )
                    for field in fields:
                        fill_field(field, answer)
                        sleep(0.2, 0.5)

                except StaleElementReferenceException:
                    pass

        except Exception as e:
            log.debug(f"Form fill error: {e}")

        # ── Next / Submit Button ───────────────────────────
        # "Submit application" button dhundho
        try:
            submit_btn = driver.find_element(
                By.CSS_SELECTOR,
                "button[aria-label='Submit application']"
            )
            submit_btn.click()
            sleep(2, 3)
            log.info(f"✅ APPLIED: {job_title}")
            return True
        except NoSuchElementException:
            pass

        # "Next" button dhundho
        try:
            next_btn = driver.find_element(
                By.CSS_SELECTOR,
                "button[aria-label='Continue to next step'], "
                "button[aria-label='Review your application']"
            )
            next_btn.click()
            sleep(1.5, 2.5)
            continue
        except NoSuchElementException:
            pass

        # "Review" button
        try:
            review_btn = driver.find_element(
                By.XPATH,
                "//button[contains(., 'Review') or contains(., 'Submit')]"
            )
            review_btn.click()
            sleep(1.5, 2.5)
            continue
        except NoSuchElementException:
            pass

        # Dismiss/Close
        try:
            close_btn = driver.find_element(
                By.CSS_SELECTOR,
                "button[aria-label='Dismiss'], button[aria-label='Cancel']"
            )
            close_btn.click()
            log.warning(f"⚠️  Modal closed without applying: {job_title}")
            return False
        except NoSuchElementException:
            break

    log.warning(f"❌ Max steps reached: {job_title}")
    return False


# ─── Apply to a Single Job ────────────────────────────────────
def apply_to_job(driver, job_card, applied_titles):
    try:
        job_card.click()
        sleep(2, 3)

        wait = WebDriverWait(driver, 10)

        # Job title nikalo
        try:
            title_el = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title, h1")
            ))
            job_title = title_el.text.strip()
        except Exception:
            job_title = "Unknown Role"

        # Company name
        try:
            company_el = driver.find_element(
                By.CSS_SELECTOR,
                ".job-details-jobs-unified-top-card__company-name, "
                ".jobs-unified-top-card__company-name"
            )
            company = company_el.text.strip()
        except Exception:
            company = "Unknown Company"

        full_title = f"{job_title} @ {company}"

        # Duplicate check
        if full_title in applied_titles:
            log.info(f"⏭️  Already applied: {full_title}")
            return False

        log.info(f"📋 Job: {full_title}")

        # Easy Apply button dhundho
        try:
            apply_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "button.jobs-apply-button[aria-label*='Easy Apply'], "
                 ".jobs-s-apply button")
            ))

            if "Easy Apply" not in apply_btn.text:
                log.info(f"⏭️  Easy Apply nahi hai: {full_title}")
                return False

            apply_btn.click()
            sleep(2, 3)

        except TimeoutException:
            log.info(f"⏭️  Apply button nahi mila: {full_title}")
            return False

        # Modal handle karo
        success = handle_easy_apply_modal(driver, full_title)
        if success:
            applied_titles.add(full_title)
            return True

    except Exception as e:
        log.error(f"Error on job card: {e}")

    return False


# ─── Save Applied Log ─────────────────────────────────────────
def save_log(applied_titles):
    log_path = f"applied_jobs_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(log_path, "w") as f:
        f.write(f"Applied Jobs — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 60 + "\n")
        for title in sorted(applied_titles):
            f.write(f"✅ {title}\n")
    log.info(f"📊 Log saved: {log_path} ({len(applied_titles)} applications)")


# ─── Main Bot Loop ────────────────────────────────────────────
def run_linkedin_bot():
    log.info("=" * 60)
    log.info("   LinkedIn Job Apply Bot — Rayees Yousuf")
    log.info("=" * 60)

    driver = get_driver()
    applied_titles = set()
    total_applied = 0
    max_apps = config.SEARCH["max_applications"]

    try:
        # Login
        if not linkedin_login(driver):
            log.error("Login failed. Ruk ke manually login karo phir restart karo.")
            input("Press Enter after manual login...")

        # Har keyword ke liye jobs search karo
        for keyword in config.SEARCH["keywords"]:
            search_jobs(driver, keyword)

            # Continuous Pagination
            page = 1
            while True:
                log.info(f"📄 Page {page} — Keyword: '{keyword}'")

                # Scroll to load all cards
                for _ in range(5):
                    driver.execute_script(
                        "document.querySelector('.jobs-search-results-list')?.scrollBy(0, 500)"
                    )
                    sleep(0.5, 1)

                cards = get_job_cards(driver)
                log.info(f"   {len(cards)} jobs mile")

                if len(cards) == 0:
                    log.info("No more jobs on this page. Moving to next keyword.")
                    break

                for i, card in enumerate(cards):
                    try:
                        success = apply_to_job(driver, card, applied_titles)
                        if success:
                            total_applied += 1
                            log.info(f"   [Total Applied: {total_applied}]")
                        sleep(2, 5)
                    except Exception as e:
                        log.error(f"Card {i} error: {e}")
                        continue

                # Next page
                try:
                    next_btn = driver.find_element(
                        By.CSS_SELECTOR,
                        "button[aria-label='View next page']"
                    )
                    next_btn.click()
                    sleep(3, 5)
                    page += 1
                except Exception:
                    log.info("Reached end of pagination for this keyword.")
                    break

            # Keyword ke beech delay
            sleep(5, 10)

    except KeyboardInterrupt:
        log.info("⛔ Bot manually stopped.")

    finally:
        save_log(applied_titles)
        log.info(f"🏁 Session complete — Total applied: {total_applied}")
        driver.quit()


if __name__ == "__main__":
    run_linkedin_bot()
