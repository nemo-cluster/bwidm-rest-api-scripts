# bwIDM REST API Scripts

This repo contains scripts to communicate with the REST API of the Reg-App from version 2.7 (not tested with earlier branches).
When a user tries to log in via SSH, the scripts provide the SSH server with the user's SSH keys

- which are [associated with the service](usr/local/bin/bwidm-rest-ssh.py) (e.g. NEMO2 jumphost)
- or [all "active" keys of the user with a predefined prefix](usr/local/bin/bwidm-rest-ssh-jumphost.py) (e.g. RZ Uni Freiburg Juphost)

In the first case, users should refer to the corresponding wiki of the service (e.g. NEMO2).
The second case is explained below.

## Howto: Use the RZ Uni Freiburg Jumphost (Testinstallation)

SSH keys can be managed via the "My SSH Pubkeys" menu entry on the bwIDM registration service.
Here you can add and revoke SSH keys.
For the RZ Uni Freiburg jumphost to work with your SSH keys, the key name must start with the following string: **UNIFR-JUMPHOST**.

To add a new ssh key, please follow these steps:

1. Login to [https://login.bwidm.de/](https://login.bwidm.de/user/ssh-keys.xhtml) and select "My SSH Pubkeys" if you are not redirected directly.
   ![SSH1](https://github.com/nemo-cluster/bwidm-rest-api-scripts/assets/190198/ece8da9f-b896-4983-8dd9-52bec492fa26)

2. Click the "Add SSH Key" or "SSH Key Hochladen" button.
   ![SSH2](https://github.com/nemo-cluster/bwidm-rest-api-scripts/assets/190198/40f6c14b-6ff7-44ef-9c49-bed30fcdea8a)

3. A new window appears.
   Enter the name of your key.
   The name must start with the string **UNIFR-JUMPHOST** (as a prefix), and paste your **SSH public key** (file <code>~/.ssh/<filename>.pub</code>) into the box labeled "SSH Key".
   **DO NOT PASTE YOUR PRIVATE SSH KEY!**
   Click on the "Add" or "Hinzufügen" button.
   ![SSH3](https://github.com/nemo-cluster/bwidm-rest-api-scripts/assets/190198/a9fd94fe-f73d-485e-b2da-fc22e9570514)

4. If verything worked, your new key will be displayed in the user interface.
   ![SSH4](https://github.com/nemo-cluster/bwidm-rest-api-scripts/assets/190198/bfed77b0-1058-4317-8241-1ba5893b710b)

**Newly added keys are valid for three months. After that, they are revoked and placed on a "revocation list" so they cannot be used again.**

As soon as your key(s) are provided, you can use the RZ uni Freiburg jumphost (test phase).

## Using the Jumphost

The RZ Uni Freiburg currently jumphost is currently only available for RUF account type "employee".
It is not allowed to log into the jumphost, it can only be used with the option '-J <jumphost>'.

Example:

```bash
ssh -J rzjump.nemo.uni-freiburg.de final.desination.uni-freiburg.de
```

You should configure your SSH client ro use the correct keys and users:

```ssh-config
Host rzjump.nemo.uni-freiburg.de
    User <uni_username>
    IdentityFile ~/.ssh/keys/id_ed25519_sk_nd_nano_bwidm_jumphost1
    IdentityFile ~/.ssh/keys/id_ed25519_sk_nd_nfc_bwidm_jumphost2
```

To configure a server to use the jumphost, you can use the "ProxyJump" configuration option:

```ssh-config
Host server*.subdom.uni-freiburg.de
    User admin
    ProxyJump rzjump.nemo.uni-freiburg.de
    IdentityFile ~/.ssh/keys/id_rsa-serversx
```

For more details, see https://github.com/nemo-cluster/jumphost#configure-your-local-ssh-client
