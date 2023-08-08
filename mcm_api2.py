import requests
from config import *

def get_switch_boot_image(username, password, url):
    try:
        response = requests.get(url, auth=(username, password))
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        json_data = response.json()
                                                    
        # Print the JSON data
        return (json_data)
                                                                            
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)

## in a config.py file specify these values:
#username = 
#password = 
#ip_addy = 'server ip'

boot_image_url = "http://{0}/api/2.0/devices/switchBootImage/2/.json".format(ip_addy)
sys_files_url = 'http://{0}/api/2.0/system_files/meta/.json'.format(ip_addy)
error_display_url ='http://{0}/api/2.0/error_display_notification_agents/.json'.format(ip_addy)
soft_restart = 'http://{0}/api/2.0/devices/command/softReset/.json'.format(ip_addy)
hard_restart = 'http://{0}/api/2.0/devices/command/hardReset/.json'.format(ip_addy)

#Test api return by checking for error_agent
response = get_switch_boot_image(username, password,error_display_url)
print(response)


#Example response :
#[{'ErrorDisplayNotificationAgent': {'id': 1, 'title': 'new_error_agent', 'decay_after_clear': 20, 'min_display_time': 20, 'is_remove_static': 1, 'is_single_instance': 1, 'modified': '1691450275861', 'created': '1691450275861'}}]




## using the api to upgrade the software on MCM9000
# First step:
# upload software package to local box

# Second step: 
# Enable this function switches which boot image to load
# get_switch_boot_image(username, password,boot_image_url)

# Third step:
# Use the function below to perform soft restart which should. 
# The restart restart should use the image from image from the Second step.
# get_switch_boot_image(username, password,soft_restart)
# Optional hard restart: 
#   get_switch_boot_image(username, password,hard_restart)
