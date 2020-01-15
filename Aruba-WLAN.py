import requests
import json
import urllib3
from getpass import getpass

# Suppress error messages for controllers without SSL certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Collect user input for our script
ip = input("Enter the IP Address of your Controller: ")
username = input("Controller Username: ")
password = None
while not password:
    password = getpass('Controller Password: ')
    password_verify = getpass('Retype your password: ')
    if password != password_verify:
        print('Passwords do not match.  Try again.')
        password = None
ssid_name = input("New SSID Name: ")
presharedkey = None
while not presharedkey:
    presharedkey = getpass('Enter the PSK for this WLAN: ')
    presharedkey_verify = getpass('Retype your PSK: ')
    if presharedkey != presharedkey_verify:
        print('PSKs do not match.  Try again.')
        presharedkey = None
vlan = input("Assign to a VLAN: ")

# Log into Aruba Controller and retrieve UIDARUBA for API access
r = requests.get(url='https://' + ip + ':4343/v1/api/login?username=' \
+ username +'&password=' + password, verify=False)
logindata = r.json()
uid = logindata['_global_result']['UIDARUBA']
cookies = {'SESSION': uid}
headers = {'content-type': 'application/json'}
print("Our UID for this sessions is: " + uid + '\n')

# Create a new VLAN
print("\nCreating VLAN \n")
newvlan = {'id': vlan}
post_vlan_id = requests.post(url='https://' + ip + \
":4343/v1/configuration/object/vlan_id?config_path=%2Fmm&UIDARUBA=" + uid, \
data=json.dumps(newvlan), headers=headers, verify=False, cookies=cookies)
print(post_vlan_id.text)

# Build AAA Profile
print("\nCreating Authentication Profiles \n")
dot1x_prof = {
  "profile-name": ssid_name + "_auth_prof"
}
post_dot1x_prof = requests.post(url='https://' + ip + \
":4343/v1/configuration/object/dot1x_auth_profile?config_path=%2Fmm&UIDARUBA=" \
+ uid, data=json.dumps(dot1x_prof), headers=headers, verify=False, \
cookies=cookies)
print(post_dot1x_prof.text)

aaa_prof = {
  "profile-name": ssid_name + "_aaa_prof",
  "default_user_role": {
    "role": "logon"
  },
  "dot1x_auth_profile": {
    "profile-name": ssid_name + "_auth_prof"
  },
}
post_aaa_prof = requests.post(url='https://' + ip + \
":4343/v1/configuration/object/aaa_prof?config_path=%2Fmm&UIDARUBA=" + uid, \
data=json.dumps(aaa_prof), headers=headers, verify=False, cookies=cookies)
print(post_aaa_prof.text)

# Build SSID profile
print("\nCreating SSID Profile \n")
ssid_prof = {
    "profile-name": ssid_name + "_ssid_prof",
    "ssid_enable": {
      "_present": bool('true'),
      "_flags": {
        "default": bool('true')
      }
    },
    "essid": {
      "essid": ssid_name
    },
    "wpa_passphrase": {
      "wpa-passphrase": presharedkey
    },
    "opmode": {
      "wpa2-psk-aes": bool('true'),
      },
}
post_ssid_prof = requests.post(url='https://' + ip + \
":4343/v1/configuration/object/ssid_prof?config_path=%2Fmm&UIDARUBA=" + uid, \
data=json.dumps(ssid_prof), headers=headers, verify=False, cookies=cookies)
print(post_ssid_prof.text)

# Build Virtual AP
print("\nCreating Virtual AP \n")
virtual_ap_prof = {
  "profile-name": ssid_name,
  "aaa_prof": {
    "profile-name": ssid_name + "_aaa_prof"
  },
  "vlan": {
    "vlan": vlan
  },
  "forward_mode": {
    "forward_mode": "tunnel"
  },
  "ssid_prof": {
    "profile-name": ssid_name + "_ssid_prof"
  }
}
post_virtual_ap_prof = requests.post(url='https://' + ip + \
":4343/v1/configuration/object/virtual_ap?config_path=%2Fmm&UIDARUBA=" + uid, \
data=json.dumps(virtual_ap_prof), headers=headers, verify=False, cookies=cookies)
print(post_virtual_ap_prof.text)

# Add to Default AP Group
print("\nAdding new WLAN to Default AP Group \n")
ap_group_prof = {
        "profile-name": "default",
        "virtual_ap": [
          {
            "profile-name": ssid_name
          }
        ]
}
headers = {'content-type': 'application/json'}
post_ap_group_prof = requests.post(url='https://' + ip + \
":4343/v1/configuration/object/ap_group?config_path=%2Fmm&UIDARUBA=" + uid, \
data=json.dumps(ap_group_prof), headers=headers, verify=False, cookies=cookies)
print(post_ap_group_prof.text)

# Save the Configuration
print("\nSaving Configuration \n")
write_memory = requests.post(url='https://' + ip + \
':4343/v1/configuration/object/write_memory?config_path=%2Fmm&UIDARUBA=' +uid, \
headers=headers, verify=False, cookies=cookies)
print(write_memory.text)

# Show the new WLAN
print("\nShow AP ESSID\n")
show_ap_essid = requests.get(url='https://' + ip + \
':4343/v1/configuration/showcommand?json=1&command=show+ap+essid&UIDARUBA=' \
+uid, headers=headers, verify=False, cookies=cookies)
print(show_ap_essid.text)
