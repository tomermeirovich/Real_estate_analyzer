from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def setup_chrome_driver():
    """Setup Chrome driver with necessary options and extensions"""
    chrome_options = Options()
    
    # Add path to your Chrome extension (.crx file)
    extension_path = os.path.abspath("ofaokhiedipichpaobibbnahnkdoiiah-1.2.0-Crx4Chrome.com.crx")
    
    # Enhanced anti-detection measures
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--enable-extensions')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    
    # Additional experimental options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # More realistic user agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    try:
        print(f"Attempting to load extension from: {extension_path}")
        chrome_options.add_extension(extension_path)
    except Exception as e:
        print(f"Error loading extension: {str(e)}")
        return None
    
    # Create Chrome driver using the system-installed chromedriver
    service = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute stealth JavaScript
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Overwrite the permissions API
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: Promise.resolve({ state: 'granted' })
            })
        });
    """)
    
    return driver

def get_csv_from_website(url, download_path):
    """Download CSV from the specified website using Chrome extension"""
    try:
        # Setup the driver
        driver = setup_chrome_driver()
        
        # Navigate to the website
        driver.get(url)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 10)
        
        # Here you'll need to add the specific steps to:
        # 1. Interact with your Chrome extension
        # 2. Trigger the CSV download
        # Example (modify according to your extension's specific elements):
        # extension_button = wait.until(EC.presence_of_element_located((By.ID, "extension-button-id")))
        # extension_button.click()
        
        # Wait for download to complete
        time.sleep(5)  # Adjust timing as needed
        
        # Close the browser
        driver.quit()
        
        return True
        
    except Exception as e:
        print(f"Error downloading CSV: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return False

def main():
    # Configure these variables
    website_url = "https://www.madlan.co.il/for-sale/%D7%A9%D7%9B%D7%95%D7%A0%D7%94-%D7%A9%D7%9B%D7%95%D7%A0%D7%94-%D7%93-%D7%91%D7%90%D7%A8-%D7%A9%D7%91%D7%A2-%D7%99%D7%A9%D7%A8%D7%90%D7%9C?tracking_search_source=new_search&marketplace=residential"  # Replace with your target website
    download_path = os.path.join(os.getcwd(), "/Users/Tommyg/Desktop/amit_gold/madlan")  # Set your download directory
    
    # Create download directory if it doesn't exist
    os.makedirs(download_path, exist_ok=True)
    
    # Download the CSV
    success = get_csv_from_website(website_url, download_path)
    
    if success:
        print("CSV downloaded successfully!")
    else:
        print("Failed to download CSV")

if __name__ == "__main__":
    main()
