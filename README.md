MCM9000 API v20 Simple Python api example
How to use:

Part 1: create config.py file specify server values
username = 'username'
password = 'password'
ip_addy = 'server ip'

Part 2: Using the api to upgrade the software on MCM9000

 First step:
 upload software package to local box

 Second step: 
 Enable this function switches which boot image to load the next image on next boot
 get_switch_boot_image(username, password,boot_image_url)

 Third step:
 Use the function below to perform soft restart which should 
 restart from image from the Second step.
 get_switch_boot_image(username, password,soft_restart)
 
 Optional hard restart: 
   get_switch_boot_image(username, password,hard_restart)



Optional API calls:
#Swtiches the current boot image to the next boot image
boot_image_url = "http://{0}/api/2.0/devices/switchBootImage/2/.json".format(ip_addy)

#Returns a list of configuration files currently available in the system.
sys_files_url = 'http://{0}/api/2.0/system_files/meta/.json'.format(ip_addy)

#Returns a single Error Display Agent configuration data.
error_display_url ='http://{0}/api/2.0/error_display_notification_agents/.json'.format(ip_addy)

#Restarts all software components. Unsaved configuration is kept.
soft_restart = 'http://{0}/api/2.0/devices/command/softReset/.json'.format(ip_addy)

#Full restart of the device. If a standalone system, configuration will return to last saved one, removing all unsaved changes. If device connected to stack, configuration will be kept, as long as at least one device on the stack stays up.
hard_restart = 'http://{0}/api/2.0/devices/command/hardReset/.json'.format(ip_addy)


