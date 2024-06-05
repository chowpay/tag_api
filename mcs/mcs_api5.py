#Gets the bearer token for api auth:
import requests
import json
import urllib3

# Suppress only the single InsecureRequestWarning from urllib3 needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Example variables
ip_address = '192.168.86.77' #MCS ip
port = '443'
username = 'Admin'
password = 'Admin'
version = '5.0'
config_url = "channels/config"


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
def get_config_response(ip_address, port, version, bearer_token,confg_url):
    # Construct the request URL
    request_url = "https://{0}:{1}/api/{2}/{3}/".format(ip_address,port,version,config_url)

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


#Bear token
token = get_bearer_token(ip_address, port, username, password, version)

if token:
    print('Bearer Token: {0}'.format(token))
    config = get_config_response(ip_address, port, version, token,config_url)
    if config:
        print('Channel Config:', json.dumps(config, indent=4))
    else:
        print('Failed to retrieve channel config')
else:
    print('Failed to retrieve Bearer Token')