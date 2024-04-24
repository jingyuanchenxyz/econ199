import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    options = Options()
    # Add any configurations to options if needed
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def request_page(license_id, driver):
    url = f"http://sbs.naic.org/solar-external-lookup/lookup/licensee/summary/{license_id}?jurisdiction=NJ&entityType=IND&licenseType=PRO"
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'apptTable')))
        table_html = driver.find_element(By.ID, 'apptTable').get_attribute('outerHTML')
        df = pd.read_html(table_html)[0]
        print(f"Data found for license ID {license_id}.")
        return df
    except Exception as e:
        print(f"Failed for license ID {license_id}. Error: {e}")
        return pd.DataFrame()

if __name__ == '__main__':
    excel_path = '/Users/jingyuanchen/Desktop/econ199/W215311_1.xlsx'
    df = pd.read_excel(excel_path)
    
    # Filter only the licenses with "Active" status
    active_licenses = df[df['LICENSE_STATUS'] == 'Active']['LICENSE_NO'].tolist()

    driver = setup_driver()  # Initialize the driver once and reuse for each request

    all_appointments = pd.DataFrame()
    test_iterations = 5  # Set a limit for testing iterations
    for count, license_id in enumerate(active_licenses):
        if count >= test_iterations:
            break  # Stop after a few iterations for testing
        df_appointments = request_page(license_id, driver)
        if not df_appointments.empty:
            df_appointments['License ID'] = license_id  # Add a new column with the License ID
            all_appointments = pd.concat([all_appointments, df_appointments], ignore_index=True)
            print(f"Data appended for license ID {license_id}.")

    driver.quit()  # Make sure to quit the driver after completing all requests

    # Move 'License ID' column to the front if it exists
    if 'License ID' in all_appointments:
        cols = ['License ID'] + [col for col in all_appointments if col != 'License ID']
        all_appointments = all_appointments[cols]

    all_appointments.to_csv('appointments_test.csv', index=False)
    print("Test complete. Data saved to 'appointments_test.csv'.")
