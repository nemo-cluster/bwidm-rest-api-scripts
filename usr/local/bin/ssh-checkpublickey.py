#!/usr/bin/env python3

import sys
import os
import re
import base64


def get_ssh_public_key(filename):
    with open(filename, "r") as file:
        content = file.read()
        key = re.findall(r"sk-ssh-ed25519@openssh.com\s+([A-Za-z0-9+/=]+)", content)
        if key:
            return key[0]
        else:
            return None


# Check if the filename is passed as an argument
if len(sys.argv) < 2:
    print(
        "Please provide the filename of a 'sk-ssh-ed25519@openssh.com' SSH Public Key as an argument."
    )
    sys.exit(1)

public_key_file = sys.argv[1]
if not os.path.isfile(public_key_file) or not os.access(public_key_file, os.R_OK):
    print(f"Invalid or unreadable file: {public_key_file}")
    sys.exit(1)

ssh_public_key = get_ssh_public_key(public_key_file)
if ssh_public_key:
    decoded_key = base64.b64decode(ssh_public_key)
    decoded_key = decoded_key[4:]  # Remove the first 4 bytes
    null_index = decoded_key.find(b"\x00")  # Find the index of the first null byte
    if null_index >= 0:
        decoded_key = decoded_key[:null_index]  # Use only the part until the null byte
    utf8_key = decoded_key.decode("utf-8")

    # Search for the string "sk-ssh-ed25519@openssh.com" in utf8_key
    match = re.search(r"sk-ssh-ed25519@openssh.com", utf8_key)
    if match:
        print("The string 'sk-ssh-ed25519@openssh.com' was found in the key.")
    else:
        print("The string 'sk-ssh-ed25519@openssh.com' was not found in the key.")
else:
    print("No 'sk-ssh-ed25519@openssh.com' SSH Public Key found.")
