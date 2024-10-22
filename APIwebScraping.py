from flask import Flask, request, jsonify
import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)


def script(state, commodity, market):
    # URL of the website with the dropdown fields
    initial_url = "https://agmarknet.gov.in/SearchCmmMkt.aspx"

    # Set up headless mode for Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument(
        "--no-sandbox")  # Bypass OS security model (required for running in some Linux environments)
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

    # Initialize the Chrome driver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open the initial URL
        driver.get(initial_url)

        print("Commodity")
        dropdown = Select(driver.find_element("id", 'ddlCommodity'))
        dropdown.select_by_visible_text(commodity)

        print("State")
        dropdown = Select(driver.find_element("id", 'ddlState'))
        dropdown.select_by_visible_text(state)

        print("Date")
        # Calculate the date 7 days ago from today
        today = datetime.now()
        desired_date = today - timedelta(days=7)
        date_input = driver.find_element(By.ID, "txtDate")
        date_input.clear()
        date_input.send_keys(desired_date.strftime('%d-%b-%Y'))

        print("Click")
        button = driver.find_element("id", 'btnGo')
        button.click()

        # Wait for the market dropdown to become visible
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'ddlMarket'))
        )

        print("Market")
        dropdown = Select(driver.find_element("id", 'ddlMarket'))
        dropdown.select_by_visible_text(market)

        print("Click")
        button = driver.find_element("id", 'btnGo')
        button.click()

        # Wait for the table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'cphBody_GridPriceData'))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract data from the table
        data_list = []
        for row in soup.find_all("tr"):
            data_list.append(row.text.replace("\n", "_").replace("  ", "").split("__"))

        jsonList = []
        for i in data_list[4:len(data_list) - 1]:
            d = {}
            d["S.No"] = i[1]
            d["City"] = i[2]
            d["Commodity"] = i[4]
            d["Min Prize"] = i[7]
            d["Max Prize"] = i[8]
            d["Model Prize"] = i[9]
            d["Date"] = i[10]
            jsonList.append(d)

    except Exception as e:
        print(f"Error occurred: {e}")
        jsonList = []

    finally:
        driver.quit()

    return jsonList


@app.route('/', methods=['GET'])
def homePage():
    dataSet = {"Page": "Home Page navigate to request page", "Time Stamp": time.time()}
    return jsonify(dataSet)


@app.route('/request', methods=['GET'])
def requestPage():
    commodityQuery = request.args.get('commodity')
    stateQuery = request.args.get('state')
    marketQuery = request.args.get('market')

    if not commodityQuery or not stateQuery or not marketQuery:
        return jsonify({"error": "Missing query parameters"})

    try:
        json_data = json.dumps(script(stateQuery, commodityQuery, marketQuery), indent=4)
        return json_data
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == '__main__':
    app.run()
