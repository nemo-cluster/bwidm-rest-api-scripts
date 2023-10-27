#!/usr/bin/python
"""Get all SSH keys from an bwIDM user matching a pre-defined pefix."""

import argparse
import configparser
import json
import os
import re
import sys

import requests

# Config file location
CONFIG_FILE = "/usr/local/etc/bwidm-rest-ssh.conf"
SSH_KEY_NAME = "UNIFR-JUMPHOST"


def exit_with_msg(exit_code, *messages):
    """Function prints message and exits."""
    for msg in messages:
        print(msg, file=sys.stderr)
    sys.exit(exit_code)


def check_user_name(ssh_user):
    """Function checks if username is valid."""
    if not re.fullmatch(r"\w{1,12}", ssh_user):
        exit_with_msg(41, f"Not a valid user name: {ssh_user}")
    return ssh_user


# Get UserID from UserName, returns UserID
def get_user_id(rest_u, rest_p, max_t, reg_h, sn, ssh_u):
    """Function takes username and returns user info."""
    try:
        response_u = requests.get(
            f"https://{reg_h}/rest/attrq/eppn/{sn}/{ssh_u}@uni-freiburg.de",
            auth=(rest_u, rest_p),
            timeout=max_t,
        )
        response_u.raise_for_status()
    except requests.exceptions.RequestException as r:
        exit_with_msg(31, f"Access denied ({r})")

    http_code_d = response_u.status_code
    if http_code_d == 200:
        user_info_d = response_u.text
        return user_info_d
    if http_code_d != 200:
        exit_with_msg(32, f"Access denied ({http_code_d})")
    return None


# Command line variables
parser = argparse.ArgumentParser(description="Process some stuff.")
parser.add_argument("ssh_user", type=check_user_name, help="SSH User Name")
args = parser.parse_args()
ssh_user: str
ssh_user = args.ssh_user

# Local user, skip AttributeQuery (Access granted)
authorized_keys_path = f"/etc/ssh/authorized_keys.d/{ssh_user}"
if os.path.exists(authorized_keys_path):
    with open(authorized_keys_path, "r", encoding="utf-8") as file:
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
    with open(CONFIG_FILE, "r", encoding="utf-8") as conf:
        max_time: int
        reg_host: str
        rest_user: str
        rest_pw: str
        ssn: str
        config.read_file(conf)
        max_time = config.getint("DEFAULT", "max_time", fallback=10)
        reg_host = config["REST"]["reg_host"]
        rest_user = config["REST"]["rest_user"]
        rest_pw = config["REST"]["rest_pw"]
        ssn = config["SSN"]["ssn"]
except OSError:
    exit_with_msg(21, f"Can not read config file {CONFIG_FILE}")

if not reg_host:
    exit_with_msg(22, "Config variable reg_host is empty")
elif not rest_user:
    exit_with_msg(23, "Config variable rest_user is empty")
elif not rest_pw:
    exit_with_msg(24, "Config variable rest_pw is empty")
elif not ssn:
    exit_with_msg(25, "Config variable SID is empty")

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
    exit_with_msg(11, f"Access was not granted (Access denied). {e}")

http_code = response.status_code
if http_code == 200:
    ssh_keys = json.loads(response.text)
    for key in ssh_keys:
        # For active keys remove "re.match"
        if re.search(SSH_KEY_NAME, key["name"]):
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
