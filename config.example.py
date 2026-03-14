# ============================================================
#  config.example.py — Copy this to config.py and fill in your details
# ============================================================

PERSONAL = {
    "first_name":   "YOUR_FIRST_NAME",
    "last_name":    "YOUR_LAST_NAME",
    "email":        "your.email@example.com",
    "phone":        "1234567890",
    "location":     "Your City, State, Country",
    "city":         "Your City",
    "state":        "Your State",
    "country":      "Your Country",
    "zip_code":     "000000",
    "linkedin_url": "https://linkedin.com/in/yourprofile",
    "resume_path":  "Your_Resume.pdf",
    "gender":       "Male",           # or Female / Non-binary / Prefer not to say
    "ethnicity":    "Asian",          # Update as applicable
    "age":          "25",
    "veteran":      "No",
    "disability":   "No",
}

# --- Platform Credentials ---
# ⚠️  NEVER commit this file with real passwords!

LINKEDIN = {
    "email":    "your.email@example.com",
    "password": "YOUR_LINKEDIN_PASSWORD",
}

INDEED = {
    "email":    "your.email@example.com",
    "password": "YOUR_INDEED_PASSWORD",
}

NAUKRI = {
    "email":    "your.email@example.com",
    "password": "YOUR_NAUKRI_PASSWORD",
}

GLASSDOOR = {
    "email":    "your.email@example.com",
    "password": "YOUR_GLASSDOOR_PASSWORD",
}

FOUNDIT = {
    "email":    "your.email@example.com",
    "password": "YOUR_FOUNDIT_PASSWORD",
}

# --- Job Search Settings ---
SEARCH = {
    "keywords": [
        "Project Coordinator",
        "Ecommerce Operations",
        "Digital Project Manager",
        # Add your target job titles here
    ],
    "location":          "India",
    "remote_only":       True,
    "easy_apply_only":   True,
    "max_applications":  30,
    "experience_level":  ["Entry Level", "Associate", "Mid-Senior Level"],
    "date_posted":       "past week",
}

# --- Concurrency & Speed ---
CONCURRENT_TABS = False
MAX_CONCURRENT_JOBS = 5

WORK_AUTH = {
    "authorized_to_work": "Yes",
    "require_sponsorship": "No",
    "notice_period":       "Immediately",
    "willing_to_relocate": "No",
    "remote_work":         "Yes",
    "us_timezone":         "Yes",
}

EDUCATION = {
    "highest_level": "Bachelor's",
    "degree":        "Your Degree",
    "university":    "Your University",
    "graduation_year": "2020",
    "gpa":           "",
}

EXPERIENCE = {
    "total_years":           "5",
    "current_company":       "Your Company",
    "current_title":         "Your Title",
    "current_salary":        "600000",
    "expected_salary":       "800000",
    "currency":              "INR",
}

# ---- Saved Q&A Answers ----
# Bot matches question keywords and auto-fills answers
SAVED_ANSWERS = {
    "english":                          "Yes",
    "speak english":                    "Yes",
    "highest education":                "Bachelor's",
    "degree":                           "Bachelor's",
    "years of experience":              "5",
    "notice period":                    "Immediately",
    "salary":                           "800000",
    "expected ctc":                     "800000",
    "current ctc":                      "600000",
    "remote":                           "Yes",
    "relocate":                         "No",
    "authorized":                       "Yes",
    "work authorization":               "Yes",
    "visa":                             "No",
    "sponsorship":                      "No",
    "disability":                       "No",
    "veteran":                          "No",
    "gender":                           "Male",
    "ethnicity":                        "Asian",
    "cover letter":                     """Dear Hiring Manager,

I am excited to apply for this position. [Customize this cover letter with your experience]

Best regards,
Your Name
your.email@example.com""",
}
