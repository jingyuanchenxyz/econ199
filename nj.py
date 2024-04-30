import concurrent.futures
import pandas as pd
import os
import signal
import sys
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

def setup_driver():
    options = Options()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def request_page(license_id, driver):
    url = f"http://sbs.naic.org/solar-external-lookup/lookup/licensee/summary/{license_id}?jurisdiction=NJ&entityType=IND&licenseType=PRO"
    driver.get(url)
    all_data = []
    try:
        page_number = 1
        while True:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'apptTable')))
            table_html = driver.find_element(By.ID, 'apptTable').get_attribute('outerHTML')
            df = pd.read_html(table_html)[0]
            all_data.append(df)
            print(f"Data found for license ID {license_id} on page {page_number}.")

            if driver.find_elements(By.CSS_SELECTOR, "li.page-item.disabled a[aria-label='Next'], li.page-item.disabled a[aria-label='Last']"):
                print("No more pages to navigate. Last page reached.")
                break

            next_button = driver.find_element(By.CSS_SELECTOR, "a[aria-label='Next']")
            driver.execute_script("arguments[0].click();", next_button)
            page_number += 1
            time.sleep(2)
    except Exception as e:
        print(f"Failed for license ID {license_id}. Error: {e}")
    finally:
        driver.quit()

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def scrape_license_data(license_id):
    if is_interrupted:
        return pd.DataFrame()  # Skip processing if interrupted
    driver = setup_driver()
    try:
        return request_page(license_id, driver)
    finally:
        driver.quit()

def get_last_processed_id(checkpoint_file):
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as file:
            last_id = file.readline()
            return last_id.strip()
    return None

def update_checkpoint(license_id, checkpoint_file):
    with open(checkpoint_file, 'w') as file:
        file.write(str(license_id))

def save_data(all_appointments, base_filename, save_counter):
    if not all_appointments.empty:
        output_csv = f"{base_filename}_{save_counter}.csv"
        all_appointments.to_csv(output_csv, index=False)
        print(f"Data saved to '{output_csv}'.")
        return save_counter + 1
    return save_counter

def signal_handler(signal, frame):
    global is_interrupted
    is_interrupted = True
    print("\nProgram interrupted! Waiting for tasks to complete before exiting...")

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    is_interrupted = False

    excel_path = '/Users/jingyuanchen/Desktop/econ199/W215311_1.xlsx'
    checkpoint_file = '/Users/jingyuanchen/Desktop/econ199/checkpoint.txt'
    base_output_csv = '/Users/jingyuanchen/Desktop/econ199/appointments'

    df = pd.read_excel(excel_path)
    licenses = df['LICENSE_NO'].tolist()
    last_processed_id = get_last_processed_id(checkpoint_file)
    start_index = licenses.index(last_processed_id) + 1 if last_processed_id else 0
    num_threads = 2
    save_counter = 1  # Initialize save counter

    all_appointments = pd.DataFrame()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {}
        for license_id in licenses[start_index:]:
            if is_interrupted:
                break  # Stop scheduling new tasks if an interrupt signal is received
            future = executor.submit(scrape_license_data, license_id)
            futures[future] = license_id

        for future in concurrent.futures.as_completed(futures):
            if is_interrupted:
                continue  # Skip processing results if interrupted
            license_id = futures[future]
            try:
                df_appointments = future.result()
                if df_appointments is not None and not df_appointments.empty:
                    df_appointments['License ID'] = license_id
                    all_appointments = pd.concat([all_appointments, df_appointments], ignore_index=True)
                    update_checkpoint(license_id, checkpoint_file)
                    if len(all_appointments) >= 1000:  # Save every 1000 records
                        save_counter = save_data(all_appointments, base_output_csv, save_counter)
                        all_appointments = pd.DataFrame()  # Reset DataFrame after saving
            except Exception as exc:
                print(f'License ID {license_id} generated an exception: {exc}')

    if not all_appointments.empty:
        save_data(all_appointments, base_output_csv, save_counter)
