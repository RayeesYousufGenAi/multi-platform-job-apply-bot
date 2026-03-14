import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor
import config

# Logging setup for orchestrator
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [MAIN] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

def print_banner():
    print("==============================================================")
    print("      MULTI-PLATFORM JOB APPLY BOT — Rayees Yousuf")
    print("==============================================================")
    print("1. LinkedIn Bot")
    print("2. Indeed Bot")
    print("3. Naukri Bot")
    print("4. Glassdoor Bot")
    print("5. Foundit (Monster) Bot")
    print("6. Run ALL Concurrently (Warning: Heavy System Load)")
    print("==============================================================")

def run_linkedin():
    try:
        from linkedin_bot import run_linkedin_bot
        log.info("Starting LinkedIn Bot...")
        run_linkedin_bot()
    except ImportError as e:
        log.error(f"Failed to load LinkedIn Bot: {e}")

def run_indeed():
    try:
        from indeed_bot import run_indeed_bot
        log.info("Starting Indeed Bot...")
        run_indeed_bot()
    except ImportError as e:
        log.error(f"Failed to load Indeed Bot: {e}. Has it been implemented?")

def run_naukri():
    try:
        from naukri_bot import run_naukri_bot
        log.info("Starting Naukri Bot...")
        run_naukri_bot()
    except ImportError as e:
        log.error(f"Failed to load Naukri Bot: {e}. Has it been implemented?")

def run_glassdoor():
    try:
        from glassdoor_bot import run_glassdoor_bot
        log.info("Starting Glassdoor Bot...")
        run_glassdoor_bot()
    except ImportError as e:
        log.error(f"Failed to load Glassdoor Bot: {e}. Has it been implemented?")

def run_foundit():
    try:
        from foundit_bot import run_foundit_bot
        log.info("Starting Foundit Bot...")
        run_foundit_bot()
    except ImportError as e:
        log.error(f"Failed to load Foundit Bot: {e}. Has it been implemented?")

def run_all_concurrently():
    log.info("Starting ALL platforms concurrently!")
    bots = [run_linkedin, run_indeed, run_naukri, run_glassdoor, run_foundit]
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        for bot in bots:
            executor.submit(bot)

def main():
    print_banner()
    choice = input("Enter your choice (1-6): ").strip()
    
    if choice == "1":
        run_linkedin()
    elif choice == "2":
        run_indeed()
    elif choice == "3":
        run_naukri()
    elif choice == "4":
        run_glassdoor()
    elif choice == "5":
        run_foundit()
    elif choice == "6":
        run_all_concurrently()
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
