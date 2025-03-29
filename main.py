from flask import Flask, render_template, jsonify

import requests
import xmltodict
import json
import time
import threading
from multiprocessing.dummy import Pool as ThreadPool 

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')


api_data_cache = {}
last_update_time = None



with open("charger.txt") as f:
    Charger_list = {name: url.replace(url,f'http://{url}/data.xml?Home') for line in f for (name, url) in [line.strip().split('\t')]}
    #print(Charger_list)
    
""" Charger_list = {
    "Charger_E_Bangkae": "http://172.19.249.243/data.xml?Home",
    "Charger_E_Bangsue": "http://172.19.248.195/data.xml?Home",
    "Charger_E_Ramkhamhaeng": "http://172.19.249.99/data.xml?Home",
    "Charger_E_SathornCity2" :	"http://172.19.250.195/data.xml?Home"
} """


def fetch_data_from_api(charger_name, charger_url):
    try:
        response = requests.get(charger_url, auth=('admin', '1234'))
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        data = xmltodict.parse(response.text)
        #print(json.dumps(data, indent=2))
        #print(f'Voltage {charger_name} : {data['data']['sys']['@ChgV']}')
        return {charger_name : data['data']['sys']['@ChgV']}
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return {charger_name: "Failed to fetch data from API"}
    
def fetch_all_apis():
    """Fetch data from all API endpoints"""
    pool = ThreadPool(8)
    return pool.starmap(fetch_data_from_api,zip(Charger_list.keys(), Charger_list.values()))
    

def update_api_data_periodically():
    """Background thread function to update API data every 10 seconds"""
    global api_data_cache, last_update_time

    while True:
        print("Fetching fresh API data...")
        api_data_cache = fetch_all_apis()
        last_update_time = time.strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(10)

@app.route('/')
def index():
    return render_template('index.html', 
                           api_data=api_data_cache, 
                           last_update=last_update_time)

@app.route('/api/data')
def get_api_data():
    """API endpoint to get the latest data via AJAX"""
    return jsonify({
        'api_data': api_data_cache,
        'last_update': last_update_time
    })

if __name__ == "__main__":
    update_thread = threading.Thread(target=update_api_data_periodically, daemon=True)
    update_thread.start()
    #api_data_cache = fetch_all_apis()
    #last_update_time = time.strftime("%Y-%m-%d %H:%M:%S")
    app.run(host='0.0.0.0', debug=True)