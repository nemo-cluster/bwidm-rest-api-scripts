#!/usr/bin/env python3
"""
Fetches all active SSH keys of a bwIDM user for a bwIDM service.
The SSH command can be used to use FIDO2 SSH keys without OTP.
"""

import argparse
import base64
import configparser
import os
import re
import sys

import requests

# Config file location
CONFIG_FILE = "/usr/local/etc/bwidm_rest_ssh.conf"
MIN_USER_ID = 900000
FIDO2_KEY_NAME = "FIDO2"


def exit_with_msg(exit_code, *messages):
    """Function prints message and exits."""
    for msg in messages:
        print(msg, file=sys.stderr)
    sys.exit(exit_code)


def check_user_name(ssh_usr):
    """Function checks if username is valid."""
    if not re.fullmatch(r"\w{1,12}", ssh_usr):
        exit_with_msg(41, f"Not a valid user name: {ssh_usr}")
    return ssh_usr


def check_user_id(uid):
    """Check if user ID is within range."""
    if re.fullmatch(r"\d{6}", uid):
        uid = int(uid)
        if uid > MIN_USER_ID:
            return uid
    exit_with_msg(31, f"Not a bwIDM User ID: {uid}")


def get_fido2_public_key(fido2_pk):
    """
    Check, if submitted key has string 'sk-ssh-ed25519@openssh.com'
    Returns base64 encoded part and comment at end
    We use bwIDM command key functionality to submit FIDO2 SSH keys
    Use 'FIDO2_KEY_NAME' for command, IP range is ignored
    Check for string 'sk-ssh-ed25519@openssh.com'
    """
    ssh_key = re.findall(
        r'command="{FIDO2_KEY_NAME}",from=".*"\s+sk-ssh-ed25519@openssh.com\s+([A-Za-z0-9+/=]+)',
        fido2_pk,
    )
    key_comment = re.findall(
        r"sk-ssh-ed25519@openssh.com\s+[A-Za-z0-9+/=]+\s+([A-Za-z0-9+/=.@-]+)",
        fido2_pk,
    )
    # If string was found, use next space separated part for SSH public key
    if ssh_key:
        return ssh_key[0], key_comment[0]
    else:
        return None


def decode_fido2_public_key(fido2_pub_key):
    """Decode submitted public key and check
    if key has string 'sk-ssh-ed25519@openssh.com'"""
    # First get base64 encoded key part [0] and comment [1]
    fido2_key = get_fido2_public_key(fido2_pub_key)
    if fido2_key:
        fido2_pub_key = fido2_key[0]
        fido2_key_comment = fido2_key[1]
        # Decode public key
        decoded_key = base64.b64decode(fido2_pub_key)
        # Remove the first 4 bytes
        decoded_key = decoded_key[4:]
        # Find the index of the first null byte
        null_index = decoded_key.find(b"\x00")
        # Use only the part until the null byte
        if null_index >= 0:
            decoded_key = decoded_key[:null_index]
        # Save results as UTF-8 text
        utf8_key = decoded_key.decode("utf-8")
        # Search for the string "sk-ssh-ed25519@openssh.com" in utf8_key
        match = re.search(r"sk-ssh-ed25519@openssh.com", utf8_key)
        # If string matches, return FIDO2 key
        if match:
            return match[0], fido2_pub_key, fido2_key_comment
        else:
            return None


# Command line variables
parser = argparse.ArgumentParser(description="Process some stuff.")
parser.add_argument("ssh_user", type=check_user_name, help="SSH User Name")
parser.add_argument("user_id", type=check_user_id, help="SSH User ID")
args = parser.parse_args()
ssh_user: str
user_id: int
ssh_user = args.ssh_user
user_id = args.user_id

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

try:
    response = requests.get(
        f"https://{reg_host}/rest/ssh-key/auth/all/{ssn}/uidnumber/{user_id}",
        auth=(rest_user, rest_pw),
        timeout=max_time,
    )
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    exit_with_msg(11, f"Access was not granted (Access denied). {e}")

http_code = response.status_code
if http_code == 200:
    ssh_keys = response.text.splitlines()
    for key in ssh_keys:
        # Simple check for FIDO2 SSH keys
        # Returns key type [0], key [1], and comment [2]
        fido2_public_key = decode_fido2_public_key(key)
        if fido2_public_key:
            print(fido2_public_key[0], fido2_public_key[1], fido2_public_key[2])
        else:
            print(key)
    sys.exit(0)
elif http_code != 200:
    exit_with_msg(12, f"Access denied ({http_code})")
