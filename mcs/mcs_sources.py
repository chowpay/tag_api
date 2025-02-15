#MCS sources
"""
This script is used to clone, delete, or clone from csv file

how to use:
1. fill out the api info
2. python mcs_sources.py
3. clone single channels
4. delete single channels
5. clone many channels from csv

see clone_channels_sample.xls
reference channel is :  in the column called

"""


#Gets the bearer token for api auth:
import requests
import json
import urllib3
import copy
import readline
import csv

# Suppress only the single InsecureRequestWarning from urllib3 needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API Example
ip_address = '192.168.86.77' #MCS ip
port = '443'
username = 'Admin'
password = 'Admin'
version = '5.0'
channel_url = "channels/config"
network_url = "networks/config"


# Gets api headers
def get_headers(token):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

#Get the bearer token
def get_bearer_token(ip_address, port, username, password, version):
    # Construct the access URL
    access_url = "https://{0}:{1}/api/{2}/auth/login".format(ip_address,port,version)

    # Define the headers
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json'
    }

    # Define the payload
    payload = {
        'username': username,
        'password': password
    }

    try:
        # Send the POST request with verify=False to bypass SSL verification
        response = requests.post(access_url, headers=headers, json=payload, verify=False)

        # Check if the request was successful
        if 200 <= response.status_code < 300:
            # Parse the response JSON
            response_json = response.json()
            # Extract the Bearer token
            bearer_token = response_json['data']['access_token']
            return bearer_token
        else:
            print('Failed to retrieve Bearer Token {0} - {1}'.format(response.status_code,response.text))
            # Handle the error case
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print('Error: {0}'.format(e))
        return None

#Get the api response
def get_config_response(ip_address, port, version, bearer_token,config_url):
    # Construct the request URL
    request_url = "https://{0}:{1}/api/{2}/{3}/".format(ip_address,port,version,config_url)
    print(f"request_url {request_url}")

    # Define the headers
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer {}'.format(bearer_token)
    }

    try:
        # Send the GET request with verify=False to bypass SSL verification
        response = requests.get(request_url, headers=headers, verify=False)

        # Check if the request was successful (any 2xx status code)
        if 200 <= response.status_code < 300:
            # Parse and return the response JSON
            return response.json()
        else:
            print("Failed to retrieve channel config: {} - {}".format(response.status_code, response.text))
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error: {}".format(e))
        return None



# List available channels
def list_channels(channels):
    print("\nAvailable Channels:")
    for i, channel in enumerate(channels["data"], start=1):
        print(f"{i}. {channel['label']}")


# Create cloning actions:

# Select a base channel for cloning
def select_base_clone(channels, action="clone"):
    list_channels(channels)
    prompt_text = "Enter the number of the channel to {}: ".format("delete" if action == "delete" else "clone")
    selected_index = int(input(prompt_text)) - 1
    if not (0 <= selected_index < len(channels["data"])):
        print("Invalid selection. Exiting.")
        return None
    return channels["data"][selected_index]


# Get network mappings (UUIDs <-> Human-Readable Labels)
def get_network_mapping(networks):
    return {net["label"]: net["uuid"] for net in networks["data"]}


# Assign networks to the cloned channel
def assign_networks_to_channel(new_channel, selected_network_uuids):
    for receiver in new_channel["receivers"]:
        for i in range(len(receiver["networks"])):
            receiver["networks"][i]["network"] = selected_network_uuids[i]


# Send API request to create a new channel
def send_create_channel_request(token, new_channel):
    payload = {"data": [new_channel]}
    api_url = f"https://{ip_address}:{port}/api/{version}/channels/config"
    response = requests.post(api_url, headers=get_headers(token), json=payload, verify=False)

    if response.status_code in [200, 201]:
        print(f"Channel '{new_channel['label']}' created successfully!")
    else:
        print(f"Failed to create channel '{new_channel['label']}'. Error: {response.text}")


# Clone a single channel
def clone_channel(token):
    print("\nCloning a Channel..")
    all_channels = get_config_response(ip_address, port, version, token, channel_url)
    networks = get_config_response(ip_address, port, version, token, network_url)

    if "data" not in all_channels or "data" not in networks:
        print("Failed to retrieve channels or networks.")
        return

    selected_channel = select_base_clone(all_channels)
    if not selected_channel:
        return

    new_channel = copy.deepcopy(selected_channel)
    default_label = selected_channel["label"]
    readline.set_startup_hook(lambda: readline.insert_text(default_label))
    new_label = input("Enter the new label for the cloned channel: ").strip()
    readline.set_startup_hook(None)

    if not new_label or new_label == selected_channel["label"]:
        print("Error: The new label cannot be empty or the same as the original.")
        return

    new_channel["label"] = new_label
    new_channel["uuid"] = None

    network_mapping = get_network_mapping(networks)
    print("\nAvailable Networks:")
    for idx, (label, uuid) in enumerate(network_mapping.items(), start=1):
        print(f"{idx}. {label} (UUID: {uuid})")

    selected_network_uuids = []
    num_networks = len(selected_channel["receivers"][0]["networks"])
    print(f"\nThis channel requires {num_networks} network(s).")

    for i in range(num_networks):
        while True:
            try:
                selected_index = int(input(f"Enter number for network {i + 1}/{num_networks}: ")) - 1
                network_list = list(network_mapping.keys())
                if 0 <= selected_index < len(network_list):
                    selected_network_uuids.append(network_mapping[network_list[selected_index]])
                    break
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Error: Please enter a number.")

    assign_networks_to_channel(new_channel, selected_network_uuids)
    send_create_channel_request(token, new_channel)

# Clone multiple channels from CSV
def clone_channels_from_csv(token, csv_file):
    print("\nCloning Channels from CSV...")

    # Step 1: Fetch all channels and networks
    all_channels = get_config_response(ip_address, port, version, token, channel_url)
    networks = get_config_response(ip_address, port, version, token, network_url)

    if "data" not in all_channels or "data" not in networks:
        print("Failed to retrieve channels or networks.")
        return

    network_mapping = get_network_mapping(networks)
    print(f"\nNetwork Mapping (UUIDs): {network_mapping}")  # Debugging line

    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            new_label = row["label"].strip()
            base_clone_label = row["base_clone"].strip()  # Read base_clone
            network_1_label = row["network_1"].strip()
            network_2_label = row["network_2"].strip()

            print(f"\nProcessing Row: {row}")  # Debugging line

            # Step 2: Find the base channel in `all_channels`
            base_clone = next((ch for ch in all_channels["data"] if ch["label"] == base_clone_label), None)
            if not base_clone:
                print(f"Error: Base channel '{base_clone_label}' not found. Skipping.")
                continue

            # Step 3: Validate if the networks exist
            if network_1_label not in network_mapping or network_2_label not in network_mapping:
                print(f"Error: One or both networks not found for {new_label}. Skipping.")
                print(f"Available Networks: {list(network_mapping.keys())}")  # Show available networks
                continue

            # Step 4: Clone the selected base channel
            new_channel = copy.deepcopy(base_clone)
            new_channel["label"] = new_label
            new_channel["uuid"] = None  # Ensure the system generates a new UUID

            # Step 5: Assign the networks
            selected_network_uuids = [network_mapping[network_1_label], network_mapping[network_2_label]]
            assign_networks_to_channel(new_channel, selected_network_uuids)

            # Step 6: Print JSON payload before sending
            print("\n==== JSON Payload for New Channel ====")
            print(json.dumps({"data": [new_channel]}, indent=4))
            print("====================================\n")

            # Step 7: Send API request
            send_create_channel_request(token, new_channel)

# Delete a Channel
def delete_channel(token):
    print("\nDeleting a Channel...")
    all_channels = get_config_response(ip_address, port, version, token, channel_url)

    if "data" not in all_channels:
        print("Failed to retrieve channels.")
        return

    selected_channel = select_base_clone(all_channels, action="delete")  # Pass "delete"
    if not selected_channel:
        return

    confirm = input(f"Are you sure you want to delete '{selected_channel['label']}'? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Deletion canceled.")
        return

    api_url = f"https://{ip_address}:{port}/api/{version}/channels/config/{selected_channel['uuid']}"
    response = requests.delete(api_url, headers=get_headers(token), verify=False)

    if response.status_code in [200, 204]:
        print(f"Channel '{selected_channel['label']}' deleted successfully!")
    else:
        print(f"Failed to delete channel. Error: {response.text}")

# Delete a channel using CSV
def delete_channels_from_csv(token, csv_file):
    print("\nDeleting Channels from CSV...")

    # Fetch all channels
    all_channels = get_config_response(ip_address, port, version, token, channel_url)

    if "data" not in all_channels:
        print("Failed to retrieve channels.")
        return

    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            delete_label = row.get("delete_channel", "").strip()  # Ensure it reads the column correctly

            # Skip empty rows
            if not delete_label:
                continue

            # Find the channel to delete
            selected_channel = next((ch for ch in all_channels["data"] if ch["label"] == delete_label), None)
            if not selected_channel:
                print(f"Error: Channel '{delete_label}' not found. Skipping.")
                continue

            delete_uuid = selected_channel["uuid"]

            # Send DELETE Request without asking for confirmation
            api_url = f"https://{ip_address}:{port}/api/{version}/channels/config/{delete_uuid}"
            response = requests.delete(api_url, headers=get_headers(token), verify=False)

            if response.status_code in [200, 204]:
                print(f"Channel '{delete_label}' deleted successfully!")
            else:
                print(f"Failed to delete channel '{delete_label}'. Error: {response.text}")



def main():

    token = get_bearer_token(ip_address, port, username, password, version)
    print(f"\n🔹 Bearer Token: {token}")  # Debugging line
    action = input("\n1. Clone a channel\n2. Delete a channel\n3. Clone multiple channels from CSV\n4. Delete channels from CSV\nEnter your choice: ")



    if token:
        if action == "1":
            clone_channel(token)
        elif action == "2":
            delete_channel(token)
        elif action == "3":
            csv_file = input("Enter CSV file path: ")
            clone_channels_from_csv(token, csv_file)
        elif action == "4":
            csv_file = input("Enter CSV file path: ")
            delete_channels_from_csv(token, csv_file)
# Run Script
if __name__== "__main__":
    main()
