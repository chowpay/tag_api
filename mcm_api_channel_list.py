## MCM9000 API v20 Simple Python api example
## How to use:

##Part 1: Fill out sample_config.py file and rename file to config.py
#username = 'Admin'
#password = 'Admin'
#ip_addy = '192.168.86.84'

#Part 2: Using the api to upgrade the software on MCM9000
#
# First step:
# upload software package to local box

# Second step: 
# Enable this function switches which boot image to load the next image on next boot
# get_switch_boot_image(username, password,boot_image_url)

# Third step:
# Use the function below to perform soft restart which should 
# restart from image from the Second step.
# get_switch_boot_image(username, password,soft_restart)
# 
# Optional hard restart: 
#   get_switch_boot_image(username, password,hard_restart)
#
##

import requests
import json
from config import *

def get_api_response(username, password, url):
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


#Optional api urls:
boot_image_url = "http://{0}/api/2.0/devices/switchBootImage/2/.json".format(ip_addy)
sys_files_url = 'http://{0}/api/2.0/system_files/meta/.json'.format(ip_addy)
error_display_url ='http://{0}/api/2.0/error_display_notification_agents/.json'.format(ip_addy)
soft_restart = 'http://{0}/api/2.0/devices/command/softReset/.json'.format(ip_addy)
hard_restart = 'http://{0}/api/2.0/devices/command/hardReset/.json'.format(ip_addy)

#channel_config = f'http://{host}/api/2.0/channels/config/{id_config}/.json'
channel_config = 'http://{0}/api/2.0/channels/config/.json'.format(ip_addy)

#Test api return by checking for error_agent
#This example uses error_display_url and prints out the response
#response = get_api_response(username, password,error_display_url)
response = get_api_response(username, password, channel_config)
#response = get_api_response(username, password,hard_restart)

json_data =json.loads(response)
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

#MCM info
mcm_source_info = {}
mcm_source_info['MCM'] = ip_addy

source_data=[]
for channel_id in channel_ids:
    channel_info_dict = {} # holds the channel data for each MCM
    channel_config_id = 'http://{0}/api/2.0/channels/config/{1}/.json'.format(ip_addy,channel_id)
    channel_id_resp = get_api_response(username, password, channel_config_id)
    channel_id_json = json.loads(channel_id_resp)
    channel_data = channel_id_json['ChannelSource']
    channel_title = channel_id_json['ChannelSource']['title']

    # Add channel info
    channel_info_dict['source_id'] = channel_id
    channel_info_dict['channel_name'] = channel_title

    ##Title
    #print('TITLE: {0}'.format(channel_title))

    #Grab the source URL or IP
    if 'main_url' in channel_data:
        #print(channel_id_json)
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

print(mcm_source_info)


#Example response :
#[{'ErrorDisplayNotificationAgent': {'id': 1, 'title': 'new_error_agent', 'decay_after_clear': 20, 'min_display_time': 20, 'is_remove_static': 1, 'is_single_instance': 1, 'modified': '1691450275861', 'created': '1691450275861'}}]
