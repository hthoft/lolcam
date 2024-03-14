import json
from datetime import datetime
import os
import subprocess

json_file_path = 'network.json'
wpa_supplicant_conf_path = '/etc/wpa_supplicant/wpa_supplicant.conf'

def update_network_password():
    today1 = datetime.now().strftime('%Y-%m-%d')
    print(f"Today's date: {today1}")
    today = str(today1)
    try:
        with open(json_file_path, 'r') as file:
            network_info = json.load(file)
            print("Loaded network info:", network_info)
            
        today_info = network_info.get(today)
        print(today_info)
        if today_info is None:
            print(f"No network info found for {today}.")
            return
        
        ssid = today_info['ssid']
        password = today_info['password']
        
        conf_content = f'''
                        ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
                        update_config=1
                        country=GB

                        network={{
                            ssid="{ssid}"
                            psk="{password}"
                            key_mgmt=WPA-PSK
                        }}
                        '''
        with open(wpa_supplicant_conf_path, 'w') as conf_file:
            conf_file.write(conf_content)
        subprocess.run(['wpa_cli', '-i', 'wlan0', 'reconfigure'])
        
        print(f"Network {ssid} password for {today} updated successfully.")
    
    except FileNotFoundError:
        print("The JSON file or wpa_supplicant.conf was not found.")
    except json.JSONDecodeError:
        print("JSON file is not properly formatted.")
    except Exception as e:
        print(f"An error occurred: {e}")

update_network_password()
