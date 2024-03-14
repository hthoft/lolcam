import json
from datetime import datetime
import os

json_file_path = 'network.json'

def update_network_password():
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        with open(json_file_path, 'r') as file:
            passwords = json.load(file)
        today_password = passwords.get(today)
        if today_password is None:
            print(f"No password found for {today}.")
            return
    
        print(f"Network password for {today} updated successfully.")
    
    except FileNotFoundError:
        print("The JSON file was not found.")
    except json.JSONDecodeError:
        print("JSON file is not properly formatted.")
update_network_password()
