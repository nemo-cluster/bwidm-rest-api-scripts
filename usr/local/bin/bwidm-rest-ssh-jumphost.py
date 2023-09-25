#!/usr/bin/env python3

import sys
import os
import re
import base64
import requests
import configparser
import argparse
import json
from datetime import datetime, timedelta


# Config file location
config_file = "/usr/local/etc/bwidm-rest-ssh.conf"
ssh_key_name = "UNIFR-JUMPHOST"


def exit_with_msg(exit_code, *messages):
    for msg in messages:
        print(msg, file=sys.stderr)
    sys.exit(exit_code)


def check_user_name(ssh_user):
    if not re.fullmatch(r"\w{1,12}", ssh_user):
        exit_with_msg(9, f"Not a valid user name: {ssh_user}")
    return ssh_user


# Get UserID from UserName, returns UserID
def get_user_id(rest_user, rest_pw, max_time, reg_host, ssn, ssh_user):
    try:
        response = requests.get(
            f"https://{reg_host}/rest/attrq/eppn/{ssn}/{ssh_user}@uni-freiburg.de",
            auth=(rest_user, rest_pw),
            timeout=max_time,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        exit_with_msg(21, f"Access was not granted (Access denied). {e}")

    http_code = response.status_code
    if http_code == 200:
        user_info = response.text
        return user_info
        sys.exit(0)
    elif http_code == 401:
        exit_with_msg(41, "Login Failed (Access denied)")
    elif http_code == 402:
        exit_with_msg(42, "Service ID not valid (Access denied)")
    elif http_code == 403:
        exit_with_msg(
            43, "No assertion resulted from the AttributeQuery (Access denied)"
        )
    elif http_code == 404:
        exit_with_msg(44, "User is not registered (Access denied)")
    elif http_code == 500:
        exit_with_msg(50, "Misconfigured service (Access denied)")
    else:
        exit_with_msg(
            19,
            f"Access was not granted (Access denied). HTTP status code is {http_code}.",
        )


# Command line variables
parser = argparse.ArgumentParser(description="Process some stuff.")
parser.add_argument("ssh_user", type=check_user_name, help="SSH User Name")
args = parser.parse_args()

ssh_user = args.ssh_user

# Local user, skip AttributeQuery (Access granted)
authorized_keys_path = f"/etc/ssh/authorized_keys.d/{ssh_user}"
if os.path.exists(authorized_keys_path):
    with open(authorized_keys_path, "r") as file:
        print(file.read())
    sys.exit(0)

# Config file example:
## [DEFAULT]
## max_time = 10
##
## [REST]
## reg_host = registration_host
## rest_pw = rest_pw
## rest_user = rest_user
##
## [SSN]
## ssn = service_name

# Read config file
config = configparser.ConfigParser()
try:
    config.read_file(open(config_file))
    max_time = config.getint("DEFAULT", "max_time", fallback=10)
    reg_host = config["REST"]["reg_host"]
    rest_user = config["REST"]["rest_user"]
    rest_pw = config["REST"]["rest_pw"]
    ssn = config["SSN"]["ssn"]
except:
    exit_with_msg(12, f"Can not read config file {config_file}")

if not reg_host:
    exit_with_msg(14, "Config variable reg_host is empty")
elif not rest_user:
    exit_with_msg(15, "Config variable rest_user is empty")
elif not rest_pw:
    exit_with_msg(16, "Config variable rest_pw is empty")
elif not ssn:
    exit_with_msg(17, "Config variable SID is empty")

user_info = json.loads(
    get_user_id(rest_user, rest_pw, max_time, reg_host, ssn, ssh_user)
)
user_id = user_info["uidNumber"]

try:
    response = requests.get(
        f"https://{reg_host}/rest/ssh-key/list/uidnumber/{user_id}/key-status/ACTIVE",
        auth=(rest_user, rest_pw),
        timeout=max_time,
    )
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    exit_with_msg(18, f"Access was not granted (Access denied). {e}")

http_code = response.status_code
if http_code == 200:
    ssh_keys = json.loads(response.text)
    for key in ssh_keys:
        # For active keys remove "re.match"
        if re.search(ssh_key_name, key["name"]):
            print(key["keyType"], key["encodedKey"], ssh_user)
    sys.exit(0)
elif http_code == 401:
    exit_with_msg(41, "Login Failed (Access denied)")
elif http_code == 402:
    exit_with_msg(42, "Service ID not valid (Access denied)")
elif http_code == 403:
    exit_with_msg(43, "No assertion resulted from the AttributeQuery (Access denied)")
elif http_code == 404:
    exit_with_msg(44, "User is not registered (Access denied)")
elif http_code == 500:
    exit_with_msg(50, "Misconfigured service (Access denied)")
else:
    exit_with_msg(
        19, f"Access was not granted (Access denied). HTTP status code is {http_code}."
    )
