#!/usr/bin/env python3

import sys
import os
import requests
import configparser
import argparse

# Config file location
config_file = "/usr/local/etc/bwidm-rest-ssh.conf"
min_user_id = 900000


def exit_with_msg(exit_code, *messages):
    for msg in messages:
        print(msg, file=sys.stderr)
    sys.exit(exit_code)


def check_user_id(user_id):
    user_id = int(user_id)
    if user_id < min_user_id:
        exit_with_msg(9, f"Not a bwIDM User ID: {user_id}")
    return user_id


# Command line variables
parser = argparse.ArgumentParser(description="Process some stuff.")
parser.add_argument("ssh_user", help="SSH User Name")
parser.add_argument("user_id", type=check_user_id, help="SSH User ID")
args = parser.parse_args()

ssh_user = args.ssh_user
user_id = args.user_id

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

try:
    response = requests.get(
        f"https://{reg_host}/rest/ssh-key/auth/all/{ssn}/uidnumber/{user_id}",
        auth=(rest_user, rest_pw),
        timeout=max_time,
    )
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    exit_with_msg(18, f"Access was not granted (Access denied). {e}")

http_code = response.status_code
if http_code == 200:
    ssh_keys = response.text.splitlines()
    for key in ssh_keys:
        print(key)
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
