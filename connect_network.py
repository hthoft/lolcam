import json
from datetime import datetime
import os
import subprocess
from network_checker import InternetChecker

json_file_path = 'network.json'
wpa_supplicant_conf_path = '/etc/wpa_supplicant/wpa_supplicant.conf'

def update_network_password():
    today = datetime.now().strftime('%Y-%m-%d')

    try:
        with open(json_file_path, 'r') as file:
            network_info = json.load(file)
            
        today_info = network_info.get(today)
        if today_info is None:
            print(f"No network info found for {today}.")
            return
        
        ssid = today_info['ssid']
        password = today_info['password']
        checker = InternetChecker(ssid=ssid, psk=password)
        
        print(f"Network {ssid} password for {today} updated successfully.")
    
    except FileNotFoundError:
        print("The JSON file or wpa_supplicant.conf was not found.")
    except json.JSONDecodeError:
        print("JSON file is not properly formatted.")
    except Exception as e:
        print(f"An error occurred: {e}")

update_network_password()
