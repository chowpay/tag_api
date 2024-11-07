## MCM9000 API v2.0 retrieving source list from MCM
## How to use:

##Fill out the information in the file `config.py`
#username = 'Admin'
#password = 'Admin'
#ip_addy = ['192.168.86.84','list of ips here'...]


import requests
import json
import socket
import os
from config import *


#Check to see if a TCP connection can be established with MCM
def is_alive (ip, port=80, timeout=2):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((ip, port))
        return True
    except socket.error:
        return False


#Create unique filename
def get_unique_filename(base_name):
    if not os.path.exists(base_name):
        return base_name
    else:
        count = 1
        while True:
            new_name = f"{base_name.split('.')[0]}_{count}.txt"
            if not os.path.exists(new_name):
                return new_name
            count += 1


#Send api request to MCM
def get_api_response(username, password, url, mcm_ip):

    #check if IP is reachable:
    if not is_alive(mcm_ip):
        print(f'MCM {mcm_ip} is not reachable')
        return None

    headers = {
        'Accept': 'application/json'  # Ensure the server returns JSON
    }
    try:
        response = requests.get(url, auth=(username, password), headers=headers)
        #print("Status Code:", response.status_code)  # Print status code for troubleshooting

        # Check if the response is JSON
        if response.headers.get('Content-Type') == 'application/json':
            json_data = response.json()
            return json_data
        else:
            #print("Response is not JSON format")
            return response.text  # Return raw text if not JSON

        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        json_data = response.json()
                                                    
        ## Print the JSON data
        #return (json_data)
                                                                            
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)


#print pretty report
def print_sources(mcm_all_sources):
    # Check if filename exists, if so increment it
    filename = get_unique_filename("MCM_sources.txt")

   # Open the file in write mode
    with open(filename, "w") as file:
        # Loop over each MCM data dictionary in the list
        for idx, data in enumerate(mcm_all_sources, 1):
            file.write(f'--- MCM Source {idx} ---\n')
            file.write(f'MCM: {data["MCM"]}\n')

            # Separate OTT and multicast sources
            ott_sources = [source for source in data['sources'] if 'OTT_url' in source]
            multicast_sources = [source for source in data['sources'] if 'channel_ip' in source]

            file.write('Sources OTT:\n')
            for source in ott_sources:
                file.write(f'- {source["channel_name"]} : {source["OTT_url"]}\n')

            file.write('\nMulticast Sources:\n')
            for source in multicast_sources:
                file.write(f'- {source["channel_name"]} : {source["channel_ip"]}\n')

            file.write('\n')


def main():

    #List of all source data from each MCM
    mcm_all_sources=[]

    #Go through each MCM and generate a source report
    for mcm_ip in ip_addy:
        print(f'mcm_ip {mcm_ip}')
        # Get source config information for all channels
        channel_config = f'http://{mcm_ip}/api/2.0/channels/config/.json'
        # MCM info
        mcm_source_info = {}
        mcm_source_info['MCM'] = mcm_ip

        #Get channel config data for MCM, if data not found move to next MCM
        try:
            response = get_api_response(username, password, channel_config, mcm_ip)
            json_data =json.loads(response)

            #Get a list of all the source IDs
            channel_ids = []
            for channel_info in json_data:
                #Gets every channel id on the MCM
                channel_ids.append(channel_info['ChannelSource']['id'])

            ##Single ID check
            #id_config = '7'
            #channel_config_id = 'http://{0}/api/2.0/channels/config/{1}/.json'.format(ip_addy,id_config)
            #channel_id_resp = get_api_response(username, password, channel_config_id)
            #print(channel_id_resp)

            ##Gets all the channel info for the MCM
            #print(channel_id_json['ChannelSource']['main_url'])

            #Keep a list of every source's data
            source_data=[]

            #Go through each channel id found
            for channel_id in channel_ids:
                channel_info_dict = {} #holds the channel data for each MCM

                #Get info on the channel id
                channel_config_id = 'http://{0}/api/2.0/channels/config/{1}/.json'.format(mcm_ip,channel_id)
                channel_id_resp = get_api_response(username, password, channel_config_id, mcm_ip)
                channel_id_json = json.loads(channel_id_resp)
                channel_data = channel_id_json['ChannelSource']
                channel_title = channel_id_json['ChannelSource']['title']

                # Add channel info
                channel_info_dict['source_id'] = channel_id
                channel_info_dict['channel_name'] = channel_title

                #Grab the source URL or IP
                if 'main_url' in channel_data:
                    main_url = channel_id_json['ChannelSource']['main_url']

                    #Add to channel_dict
                    channel_info_dict['OTT_url'] = main_url
                elif 'ip_address' in channel_data:
                    channel_ip = channel_data['ip_address']
                    channel_port = channel_data['port']
                    channel_ip = f'{channel_ip}:{channel_port}'
                    channel_ssm_ip = channel_data['ssm_ip_address']

                    #Add to channel_dict
                    channel_info_dict['channel_ip'] = channel_ip
                    channel_info_dict['ssm_ip'] = channel_ssm_ip

                source_data.append(channel_info_dict)
                mcm_source_info['sources'] = source_data


            mcm_all_sources.append(mcm_source_info)

        #Move on to next MCM if there is no data
        except Exception as e:
            print(f'Unable to get response from MCM {mcm_ip}\n An error occurred: {e}\nSkipping to next MCM')

    # Generate report
    print_sources(mcm_all_sources)

        #Example response :
        #[{'ErrorDisplayNotificationAgent': {'id': 1, 'title': 'new_error_agent', 'decay_after_clear': 20, 'min_display_time': 20, 'is_remove_static': 1, 'is_single_instance': 1, 'modified': '1691450275861', 'created': '1691450275861'}}]

if __name__ == "__main__":
    main()
