import subprocess

def connect_to_eduroam(ssid, username, password):
    """
    Connects to a WPA3-Enterprise network using nmcli.
    """
    try:
        # Check if NetworkManager is running
        subprocess.run(["systemctl", "is-active", "--quiet", "NetworkManager"], check=True)
        print("NetworkManager is running.")

        # Delete existing connection (if any)
        subprocess.run(["nmcli", "connection", "delete", ssid], check=False)
        print(f"Deleted any existing configuration for {ssid}.")

        # Create a new connection
        command = [
            "nmcli", "connection", "add", "type", "wifi",
            "ssid", ssid,
            "name", ssid,
            "--",
            "802-1x.eap", "peap",
            "802-1x.identity", username,
            "802-1x.password", password,
            "802-1x.phase2-auth", "mschapv2",
            "wifi-sec.key-mgmt", "wpa-eap"
        ]
        subprocess.run(command, check=True)
        print(f"Configured network {ssid}.")

        # Bring up the connection
        subprocess.run(["nmcli", "connection", "up", ssid], check=True)
        print(f"Connected to {ssid} successfully!")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Network credentials
    network_ssid = "eduroam"
    username = "396102@net.aau.dk"
    password = "sahsnxjydrhmjgi"

    # Connect to the network
    connect_to_eduroam(network_ssid, username, password)
