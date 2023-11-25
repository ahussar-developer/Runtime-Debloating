#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def click_link(driver, ref_name):
        # Wait for up to 10 seconds until the element is clickable
    try:
        link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f'//a[@href="#{ref_name}"]'))
        )

        # Get the current URL before clicking the link
        current_url_before_click = driver.current_url

        # Click the link using JavaScript
        # driver.execute_script("arguments[0].click();", link)

        # Use regular click method
        link.click()
        
        # Wait for the URL to change
        WebDriverWait(driver, 10).until(
            EC.url_changes(current_url_before_click)
        )

        print(f"{ref_name} link clicked successfully!")

        # Wait for the URL to contain "intro"
        try:
            WebDriverWait(driver, 10).until(
                EC.url_contains(f"{ref_name}")
            )
            print(f"URL change to '{ref_name}' occurred after link click!")
        except Exception as e:
            print(f"Error: {e}")


    except Exception as e:
        print(f"Error: {e}")

def main():
    # Set up Chromium in headless mode
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')  # Disable sandboxing

    # Path to your Chromium binary (if needed)
    # chrome_options.binary_location = '/path/to/chromium'

    # Initialize the WebDriver with Chromium options
    driver = webdriver.Chrome(options=chrome_options)

    # Navigate to the webpage
    driver.get("http://127.0.0.1:8080/index.html")

    click_link(driver, "intro")
    click_link(driver, "contact")
    click_link(driver, "work")
    click_link(driver, "about")

    # Perform any other actions as needed

    # Close the browser
    driver.quit()

if __name__ == "__main__":
    main()