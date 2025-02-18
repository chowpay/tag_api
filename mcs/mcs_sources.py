#MCS Sources
#02152025 by LazyTam

"""
This script is used to clone or delete channels (sources) individually or from csv file

The use case for my script is that I have 8 MCMs each receiver is either red-1/blue-1 or red-2/blue-2
the deployment is 2110 and requires 12 sources per receiver = 96 total receivers. The only difference between
this set is the labels and alternating networks. Any other feature besides these 3 things will require additional mods


Before cloning:
1. you must have an existing channel to clone from
2. you must have existing networks defined (RED-1/2 BLUE-1/2 or default NIC#)

For cloning both mass or single clone really does 2 things:
1. This clones everything in a source(aka channel, receiver) except the uuid, which is left to the system to handle
2. this particular script only clones the source and lets you change the label (channel name) and the receiver networks


how to use:
1. fill out the api info in the script with the login info and the mcs ip
2. follow the prompt when selecting:
    1. clone
    2. delete
3. mass changes:
    1. clone from csv : sample file clone_channels_sample.csv
    2. delete from csv : delete_channels_sample.csv

Based off of api documentation here:
https://tag.atlassian.net/wiki/spaces/UPGRADES/pages/488178726/v5.0_Channel+Config
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

#Sources/Receivers/Channels
channel_url = "channels/config"
network_url = "networks/config"

#Outputs
output_url = "outputs/config"  # New API endpoint for outputs


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


# List all outputs
def list_outputs(outputs):
    print("\nAvailable Outputs:")
    for i, output in enumerate(outputs["data"], start=1):
        print(f"{i}. {output['label']}")



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


# Select base output for cloning:
def select_base_output(outputs, action="clone"):
    list_outputs(outputs)
    prompt_text = "Enter the number of the output to {}: ".format("delete" if action == "delete" else "clone")
    selected_index = int(input(prompt_text)) - 1
    if not (0 <= selected_index < len(outputs["data"])):
        print("Invalid selection. Exiting.")
        return None
    return outputs["data"][selected_index]




# Get network mappings (UUIDs <-> Human-Readable Labels)
def get_network_mapping(networks):
    return {net["label"]: net["uuid"] for net in networks["data"]}


# Assign networks to the cloned channel
def assign_networks_to_channel(new_channel, selected_network_uuids):
    for receiver in new_channel["receivers"]:
        for i in range(len(receiver["networks"])):
            receiver["networks"][i]["network"] = selected_network_uuids[i]


# Send API request to create a new channel (source)
def send_create_channel_request(token, new_channel):
    payload = {"data": [new_channel]}
    api_url = f"https://{ip_address}:{port}/api/{version}/channels/config"
    response = requests.post(api_url, headers=get_headers(token), json=payload, verify=False)

    if response.status_code in [200, 201]:
        print(f"Channel '{new_channel['label']}' created successfully!")
    else:
        print(f"Failed to create channel '{new_channel['label']}'. Error: {response.text}")


# Create outputs
def send_create_output_request(token, new_output):
    payload = {"data": [new_output]}
    api_url = f"https://{ip_address}:{port}/api/{version}/{output_url}"
    response = requests.post(api_url, headers=get_headers(token), json=payload, verify=False)

    if response.status_code in [200, 201]:
        print(f"Output '{new_output['label']}' created successfully!")
    else:
        print(f"Failed to create output '{new_output['label']}'. Error: {response.text}")


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

    #using deepcopy copies the object into a new part of the memory so reference list is not effected
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


# Clone single output
def clone_output(token):
    print("\nCloning an Output..")
    all_outputs = get_config_response(ip_address, port, version, token, output_url)

    if "data" not in all_outputs:
        print("Failed to retrieve outputs.")
        return

    selected_output = select_base_output(all_outputs)
    if not selected_output:
        return

    new_output = copy.deepcopy(selected_output)
    default_label = selected_output["label"]
    readline.set_startup_hook(lambda: readline.insert_text(default_label))
    new_label = input("Enter the new label for the cloned output: ").strip()
    readline.set_startup_hook(None)

    if not new_label or new_label == selected_output["label"]:
        print("Error: The new label cannot be empty or the same as the original.")
        return

    new_output["label"] = new_label
    new_output["uuid"] = None  # Reset UUID for system-generated one

    # Step 5: Print JSON before sending
    print("\n==== JSON Payload for New Output ====")
    print(json.dumps({"data": [new_output]}, indent=4))
    print("====================================\n")

    # Step 6: Send API request
    send_create_output_request(token, new_output)



# Clone multiple channels from CSV

def clone_outputs_from_csv(token, csv_file):
    print("\nCloning Outputs from CSV...")

    # Step 1: Fetch all outputs and networks
    all_outputs = get_config_response(ip_address, port, version, token, output_url)
    networks = get_config_response(ip_address, port, version, token, network_url)

    ##TS stuff, create an output for 2110 Template, that should go to the top [0] below pulls the channel data for it
    #print(f"{all_outputs['data'][0]}")
    #exit()

    if "data" not in all_outputs:
        print("Failed to retrieve outputs.")
        return

    # Map the network name to the UUIDs
    network_mapping = {net["label"]: net["uuid"] for net in networks["data"]}
    print(f'Network Mapping (UUIDs): {network_mapping}')  # Debugging

    grouped_outputs = {}

    with open(csv_file, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)

        for row in reader:
            print(row)
            new_label = row["label"].strip()
            base_clone_label = row["base_clone"].strip()
            stream_type = row["stream_type"].strip()
            work_mode = row.get("work_mode", "").strip()  # Optional in CSV

            # Dynamically extract all networks, IP addresses, ports, and TTLs
            network_columns = [col for col in row.keys() if col.startswith("network_")]
            ip_columns = [col for col in row.keys() if col.startswith("ip_address_")]
            port_columns = [col for col in row.keys() if col.startswith("port_")]
            ttl_columns = [col for col in row.keys() if col.startswith("ttl_")]

            print(f"\nProcessing Row: {row}")  # Debugging line

            # Step 2: Find or create the base output
            if new_label not in grouped_outputs:
                base_clone = next((out for out in all_outputs["data"] if out["label"] == base_clone_label), None)
                if not base_clone:
                    print(f"Error: Base output '{base_clone_label}' not found. Skipping.")
                    continue

                # Step 3: Clone the selected base output
                new_output = copy.deepcopy(base_clone)
                new_output["label"] = new_label
                new_output["uuid"] = None  # Ensure system assigns a new UUID
                new_output["stream"]["senders"] = []  # Reset senders

                grouped_outputs[new_label] = new_output  # Store it for later modification

            # Step 4: Assign new IPs if provided
            cloned_output = grouped_outputs[new_label]

            # Step 5: Create a new sender entry for this stream type
            sender_entry = {
                "uuid": None,  # Let the system generate a UUID
                "stream_type": stream_type,
                "networks": []
            }

            # Step 6: Preserve important fields from base clone
            base_sender = next((s for s in base_clone["stream"]["senders"] if s["stream_type"] == stream_type), None)
            if base_sender:
                sender_entry["null_padding"] = base_sender.get("null_padding", False)  # Default False
                sender_entry["transport_mode"] = base_sender.get("transport_mode", "SPTS/UDP")  # Default for MPEG-TS
                sender_entry["latency_mode"] = base_sender.get("latency_mode", "5 Frames")
                sender_entry["payload_type"] = base_sender.get("payload_type", None)

                # Work mode handling
                """ 
                Valid work modes : 6G/12G-SDI  (even when the template has it set to 12G-SDI)
                This is because  6 for 25/29.97 FPS and 12 for 50/59.94 
                Work_modes is only for 2110 stuffs not mpeg TS
                """
                if work_mode:
                    sender_entry["work_mode"] = work_mode  # Use CSV value
                elif "work_mode" in base_sender:
                    sender_entry["work_mode"] = base_sender["work_mode"]  # Default to base clone

            # Step 7: Assign networks, IPs, Ports, and TTLs
            for j in range(len(network_columns)):
                net_col = network_columns[j]
                ip_col = ip_columns[j] if j < len(ip_columns) else None
                port_col = port_columns[j] if j < len(port_columns) else None
                ttl_col = ttl_columns[j] if j < len(ttl_columns) else None

                if net_col in row and row[net_col].strip() in network_mapping:
                    network_uuid = network_mapping[row[net_col].strip()]
                    network_entry = {
                        "network": network_uuid,
                        "enabled": True  # Always enable networks
                    }

                    if ip_col and ip_col in row and row[ip_col].strip():
                        network_entry["ip_address"] = row[ip_col].strip()

                    if port_col and port_col in row and row[port_col].strip():
                        network_entry["port"] = int(row[port_col].strip())

                    if ttl_col and ttl_col in row and row[ttl_col].strip():
                        network_entry["ttl"] = int(row[ttl_col].strip())
                    else:
                        # Default to base sender's TTL if no CSV value
                        base_network = base_sender["networks"][j] if base_sender and j < len(base_sender["networks"]) else None
                        if base_network and "ttl" in base_network:
                            network_entry["ttl"] = base_network["ttl"]

                    sender_entry["networks"].append(network_entry)

            # Append sender to the cloned output
            cloned_output["stream"]["senders"].append(sender_entry)

    # Step 8: Print out the JSON
    for label, output_data in grouped_outputs.items():
        print("\n==== JSON Payload for New Output ====")
        print(json.dumps({"data": [output_data]}, indent=4))
        print("====================================\n")

        # Step 9: Send API request
        send_create_output_request(token, output_data)



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


# Delete output
def delete_output(token):
    print("\nDeleting an Output...")
    all_outputs = get_config_response(ip_address, port, version, token, output_url)

    if "data" not in all_outputs:
        print("Failed to retrieve outputs.")
        return

    selected_output = select_base_output(all_outputs, action="delete")
    if not selected_output:
        return

    confirm = input(f"Are you sure you want to delete '{selected_output['label']}'? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Deletion canceled.")
        return

    api_url = f"https://{ip_address}:{port}/api/{version}/{output_url}/{selected_output['uuid']}"
    response = requests.delete(api_url, headers=get_headers(token), verify=False)

    if response.status_code in [200, 204]:
        print(f"Output '{selected_output['label']}' deleted successfully!")
    else:
        print(f"Failed to delete output. Error: {response.text}")

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


# Delete outputs
def delete_outputs_from_csv(token, csv_file):
    print("\nDeleting Outputs from CSV...")

    # Fetch all outputs
    all_outputs = get_config_response(ip_address, port, version, token, output_url)

    if "data" not in all_outputs:
        print("Failed to retrieve outputs.")
        return

    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            delete_label = row.get("delete_output", "").strip()

            if not delete_label:
                continue

            selected_output = next((out for out in all_outputs["data"] if out["label"] == delete_label), None)
            if not selected_output:
                print(f"Error: Output '{delete_label}' not found. Skipping.")
                continue

            delete_uuid = selected_output["uuid"]
            api_url = f"https://{ip_address}:{port}/api/{version}/{output_url}/{delete_uuid}"
            response = requests.delete(api_url, headers=get_headers(token), verify=False)

            if response.status_code in [200, 204]:
                print(f"Output '{delete_label}' deleted successfully!")
            else:
                print(f"Failed to delete output. Error: {response.text}")


def main():
    token = get_bearer_token(ip_address, port, username, password, version)

    print("""
    Sources:
    1. Channel - Clone
    2. Channel - Delete
    3. Channel - Clone with CSV
    4. Channel - Delete with CSV

    Outputs:
    5. Output - Clone
    6. Output - Delete
    7. Output - Clone with CSV
    8. Output - Delete with CSV
    """)

    action = input("Enter your choice: ").strip()

    # Process user's choice
    if token:
        if action == "1":
            clone_channel(token)
        elif action == "2":
            delete_channel(token)
        elif action == "3":
            csv_file = input("Enter CSV file path: ").strip()
            clone_channels_from_csv(token, csv_file)
        elif action == "4":
            csv_file = input("Enter CSV file path: ").strip()
            delete_channels_from_csv(token, csv_file)
        elif action == "5":
            clone_output(token)
        elif action == "6":
            delete_output(token)
        elif action == "7":
            csv_file = input("Enter CSV file path: ").strip()
            clone_outputs_from_csv(token, csv_file)
        elif action == "8":
            csv_file = input("Enter CSV file path: ").strip()
            delete_outputs_from_csv(token, csv_file)
        else:
            print("Invalid choice. Please enter a number from the menu.")
# Run Script
if __name__== "__main__":
    main()
