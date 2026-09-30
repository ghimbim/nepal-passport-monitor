# -*- coding: utf-8 -*-

import os
import re
import time
import datetime
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

PORTAL_URL = "https://online.nepalpassport.gov.np/"

TARGET_PROVINCE = "Lumbini"
TARGET_DISTRICT = "Rupandehi"
TARGET_OFFICE = "Butwal"

TIME_PATTERN = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


# ─────────────────────────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────────────────────────

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
        },
        timeout=20,
    )

    response.raise_for_status()

    log("Telegram notification sent successfully.")


# ─────────────────────────────────────────────────────────────────────────────
# CHROME
# ─────────────────────────────────────────────────────────────────────────────

def create_driver():
    options = webdriver.ChromeOptions()

    # GitHub Actions has no visible desktop.
    options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    options.add_argument("--window-size=1920,1080")

    options.add_argument("--disable-blink-features=AutomationControlled")

    options.add_argument("--autoplay-policy=no-user-gesture-required")

    options.add_experimental_option(
        "excludeSwitches",
        ["enable-automation"]
    )

    options.add_experimental_option(
        "useAutomationExtension",
        False
    )

    options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.sound": 1,
        }
    )

    driver = webdriver.Chrome(options=options)

    return driver


# ─────────────────────────────────────────────────────────────────────────────
# DROPDOWN
# ─────────────────────────────────────────────────────────────────────────────

def pick_dropdown(driver, wait, dropdown_id, option_text):
    """Open a PrimeReact dropdown and select the requested option."""

    dropdown = wait.until(
        EC.element_to_be_clickable((By.ID, dropdown_id))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        dropdown,
    )

    time.sleep(0.5)

    dropdown.click()

    time.sleep(0.8)

    option = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                f"//li[contains(@class,'p-dropdown-item') "
                f"and contains(normalize-space(),'{option_text}')]",
            )
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        option,
    )

    time.sleep(0.3)

    option.click()

    time.sleep(1.5)


# ─────────────────────────────────────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────

def navigate_to_calendar(driver, wait):

    log("Opening Nepal Passport portal...")

    driver.get(PORTAL_URL)

    time.sleep(3)

    # Apply without account
    log("Clicking 'Apply without an account'...")

    button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//div[contains(@class,'homeEnrollBtn')]"
                "[.//*[contains(text(),'Apply without')]]",
            )
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        button,
    )

    button.click()

    time.sleep(1.5)

    # Confirmation dialog
    log("Confirming dialog...")

    continue_button = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.account-dialog-continue-btn")
        )
    )

    continue_button.click()

    time.sleep(2.5)

    # First issuance
    log("Selecting 'First issuance (New)'...")

    cards = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".usecase-card")
        )
    )

    cards[0].click()

    time.sleep(2)

    # Ordinary 34 pages
    log("Selecting 'Ordinary 34 pages'...")

    option_34 = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//label[contains(.,'Ordinary 34 pages')]",
            )
        )
    )

    option_34.click()

    time.sleep(1)

    # Next
    log("Clicking Next...")

    next_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[@aria-label='Next' "
                "and not(contains(@class,'p-disabled'))]",
            )
        )
    )

    next_button.click()

    time.sleep(1.5)

    # Agree
    log("Accepting terms...")

    agree_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[@aria-label='I agree']")
        )
    )

    agree_button.click()

    time.sleep(2.5)

    # Location
    log(
        f"Selecting location: "
        f"{TARGET_PROVINCE} > "
        f"{TARGET_DISTRICT} > "
        f"{TARGET_OFFICE}"
    )

    pick_dropdown(
        driver,
        wait,
        "amsProvince",
        TARGET_PROVINCE,
    )

    pick_dropdown(
        driver,
        wait,
        "amsDistrict",
        TARGET_DISTRICT,
    )

    pick_dropdown(
        driver,
        wait,
        "amsProvider",
        TARGET_OFFICE,
    )

    # Calendar
    log("Proceeding to calendar...")

    location_next = wait.until(
        EC.element_to_be_clickable(
            (By.ID, "nextButton")
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        location_next,
    )

    time.sleep(0.5)

    location_next.click()

    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".p-datepicker")
        )
    )

    time.sleep(3)

    log("Calendar successfully loaded.")


# ─────────────────────────────────────────────────────────────────────────────
# DOM HELPER
# ─────────────────────────────────────────────────────────────────────────────

def element_key(driver, element):

    try:
        return driver.execute_script(
            """
            var e = arguments[0], path = [];

            while (e.parentNode) {
                path.unshift(
                    Array.prototype.indexOf.call(
                        e.parentNode.children,
                        e
                    )
                );

                e = e.parentNode;
            }

            return path.join('-');
            """,
            element,
        )

    except Exception:
        return element.id


# ─────────────────────────────────────────────────────────────────────────────
# CALENDAR DATES
# ─────────────────────────────────────────────────────────────────────────────

def get_calendar_dates(driver):

    selectors = [
        ".p-datepicker table td:not(.p-datepicker-other-month) > span:not(.p-disabled)",
        ".p-datepicker table td:not(.p-datepicker-other-month) > span[data-p-disabled='false']",
        ".p-datepicker table td:not(.p-datepicker-other-month) > span.p-highlight",
    ]

    seen = set()
    result = []

    for selector in selectors:

        try:

            elements = driver.find_elements(
                By.CSS_SELECTOR,
                selector,
            )

            for element in elements:

                if not element.is_displayed():
                    continue

                classes = (
                    element.get_attribute("class")
                    or ""
                ).lower()

                data_disabled = (
                    element.get_attribute("data-p-disabled")
                    or ""
                ).lower()

                aria_disabled = (
                    element.get_attribute("aria-disabled")
                    or ""
                ).lower()

                if "p-disabled" in classes:
                    continue

                if data_disabled == "true":
                    continue

                if aria_disabled == "true":
                    continue

                key = element_key(driver, element)

                if key not in seen:

                    seen.add(key)
                    result.append(element)

        except Exception:
            pass

    if result:
        return result

    # Generic fallback
    fallback_selectors = [
        "td:not([class*='disabled']):not([class*='other']) > span:not([class*='disabled'])",
        ".rdp-day:not(.rdp-day_disabled):not(.rdp-day_outside)",
        "button[class*='date']:not([disabled])",
    ]

    for selector in fallback_selectors:

        try:

            elements = driver.find_elements(
                By.CSS_SELECTOR,
                selector,
            )

            for element in elements:

                if not element.is_displayed():
                    continue

                key = element_key(driver, element)

                if key not in seen:

                    seen.add(key)
                    result.append(element)

        except Exception:
            pass

    return result


# ─────────────────────────────────────────────────────────────────────────────
# TIME SLOTS
# ─────────────────────────────────────────────────────────────────────────────

def get_time_slots(driver):

    def is_disabled(element):

        try:

            classes = (
                element.get_attribute("class")
                or ""
            ).lower()

            if any(
                word in classes
                for word in (
                    "p-disabled",
                    "disabled",
                    "booked",
                    "unavailable",
                    "closed",
                )
            ):
                return True

            if (
                element.get_attribute("aria-disabled")
                or ""
            ).lower() == "true":
                return True

            placeholder = driver.execute_script(
                """
                return arguments[0]
                    .closest('.timeslot-placeholder')
                    !== null;
                """,
                element,
            )

            return bool(placeholder)

        except Exception:

            return False

    def visible_text(element):

        try:

            values = [
                element.text,
                element.get_attribute("aria-label") or "",
                element.get_attribute("title") or "",
                element.get_attribute("value") or "",
            ]

            return " ".join(
                value for value in values if value
            ).strip()

        except Exception:

            return ""

    def has_clock_time(element):

        return bool(
            TIME_PATTERN.search(
                visible_text(element)
            )
        )

    selectors = [
        ".time-grid .time-item",
        ".time-item",
        ".time-slot .time-item",
        ".time-grid > *",
        "div[class*='time-item']",
        "div[class*='slot-item']",
        ".time-slot .p-button",
        ".time-slot button",
        ".time-slot [role='button']",
        "button[class*='slot']",
        "button[class*='time']",
        ".timeslot button",
        ".slot-item",
        "[class*='timeSlot'] button",
        "[class*='time_slot'] button",
    ]

    seen = set()
    result = []

    for selector in selectors:

        try:

            elements = driver.find_elements(
                By.CSS_SELECTOR,
                selector,
            )

            for element in elements:

                if not element.is_displayed():
                    continue

                if is_disabled(element):
                    continue

                if not has_clock_time(element):
                    continue

                key = element_key(driver, element)

                if key not in seen:

                    seen.add(key)
                    result.append(element)

        except StaleElementReferenceException:

            pass

        except Exception:

            pass

    return result


# ─────────────────────────────────────────────────────────────────────────────
# NO-SLOT DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def page_says_no_slots(driver):

    try:

        source = driver.page_source.lower()

        phrases = [
            "no available time",
            "no slot",
            "slot not available",
            "slot upalabdha chaina",
            "slot upalbdha chaina",
            "available chaina",
            "appointment chaina",
            "समय उपलब्ध छैन",
        ]

        if any(
            phrase in source
            for phrase in phrases
        ):
            return True

        if (
            "अपोइन्टमेन्ट" in source
            and "छैन" in source
        ):
            return True

        return False

    except Exception:

        return False


# ─────────────────────────────────────────────────────────────────────────────
# SLOT CHECK
# ─────────────────────────────────────────────────────────────────────────────

def check_calendar_for_slots(driver):

    dates = get_calendar_dates(driver)

    if not dates:

        return (
            False,
            "No active/available dates found on calendar",
        )

    log(
        f"Found {len(dates)} active calendar date(s). "
        f"Checking each..."
    )

    for index, element in enumerate(dates):

        try:

            label = (
                element.text.strip()
                or element.get_attribute("aria-label")
                or element.get_attribute("data-date")
                or f"date#{index + 1}"
            ).strip()

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                element,
            )

            time.sleep(0.3)

            try:
                element.click()

            except Exception:

                driver.execute_script(
                    "arguments[0].click();",
                    element,
                )

            time.sleep(3)

            slots = get_time_slots(driver)

            if slots:

                if page_says_no_slots(driver):

                    log(
                        f"Date '{label}': page indicates "
                        f"unavailable — skipping"
                    )

                    continue

                time.sleep(0.8)

                confirmed_slots = get_time_slots(driver)

                if not confirmed_slots:
                    continue

                if page_says_no_slots(driver):
                    continue

                slot_labels = [
                    slot.text.strip()
                    for slot in confirmed_slots
                    if slot.text.strip()
                ][:10]

                detail = (
                    f"Date '{label}' has "
                    f"{len(confirmed_slots)} real time slot(s)!"
                    f" [{', '.join(slot_labels)}]"
                )

                return True, detail

            no_slot = page_says_no_slots(driver)

            log(
                f"Date '{label}': "
                f"{'no-slot message shown' if no_slot else 'no time slots'}"
            )

        except StaleElementReferenceException:

            log(
                f"Date #{index + 1} became stale, skipping."
            )

        except Exception as error:

            log(
                f"Date #{index + 1} check error: {error}"
            )

    return (
        False,
        f"Checked {len(dates)} active date(s) - "
        f"no time slots available",
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():

    log("=" * 65)
    log("Nepal Passport Appointment Monitor")
    log(
        f"Target: {TARGET_PROVINCE} > "
        f"{TARGET_DISTRICT} > "
        f"{TARGET_OFFICE}"
    )
    log("=" * 65)

    driver = None

    try:

        driver = create_driver()

        wait = WebDriverWait(
            driver,
            30,
        )

        navigate_to_calendar(
            driver,
            wait,
        )

        found, details = check_calendar_for_slots(
            driver
        )

        if found:

            log("")
            log("🚨 APPOINTMENT SLOT FOUND!")
            log(details)

            message = (
                "🚨 NEPAL PASSPORT APPOINTMENT SLOT AVAILABLE!\n\n"
                f"Province: {TARGET_PROVINCE}\n"
                f"District: {TARGET_DISTRICT}\n"
                f"Office: {TARGET_OFFICE}\n\n"
                f"{details}\n\n"
                f"Open the Nepal Passport portal immediately:\n"
                f"{PORTAL_URL}"
            )

            send_telegram(message)

        else:

            log("No appointment slot available.")
            log(details)

    except Exception as error:

        log(f"ERROR: {error}")

        # Notify us about unexpected failures too.
        try:

            send_telegram(
                "⚠️ Nepal Passport monitor encountered an error.\n\n"
                f"{error}"
            )

        except Exception:

            log(
                "Could not send Telegram error notification."
            )

        raise

    finally:

        if driver is not None:

            try:
                driver.quit()

            except Exception:
                pass

    log("Check complete.")


if __name__ == "__main__":
    main()
