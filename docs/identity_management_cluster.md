# Identity management cluster

## Setup

Create a new identity manager cluster in the [JASMIN cloud portal](https://cloud.jasmin.ac.uk/):

1. Login using your JASMIN user credentials and navigate to your external cloud tenancy
2. Click the clusters tab once it appears
3. Click the new cluster button
4. Pick the identity manager cluster type and provide it with:

    * Cluster name: `identity`
    * External IP: `(pick one of the available options)`
    * Admin password: `(provide a password)`
    * Admin IP ranges: `(provide an IP range)`
    * FreeIPA size: `j3.small`
    * Keycloak size: `j3.small`
    * Gateway size: `j3.small`
    * Gateway domain: `(empty)`

    > Note: it currently can't handle upper case letters in the name

    > Cluster creation takes around 20 minutes.

5. Create an ssh key pair (you can follow the [JASMIN guide](https://help.jasmin.ac.uk/article/185-generate-ssh-key-pair) for this)

6. Login to the FreeIPA interface with the admin user at `https://<your-hyphenated-external-ip>.sslip.io/`

    > Note: if you get a login popup in your browser, cancel it. 

7. Add the public key to the admin user in FreeIPA

## Adding a user

To add a non admin user:

1. Login to the FreeIPA interface with the admin user
2. Under the `Identity` and `Users` tab, click `Add` to add a new user
3. Give them a `User login`, `First name`, `Last name`, and temporary `password` and click `Add`
4. Select the user and navigate to their `User Groups` tab
5. Click `Add` and add them to the `pangeo_notebook_users` group
6. Ask them to login and reset their password (I'd recommend using their temporary credentials to configure their notebook before doing this)

For an admin user, you'll also need to add them to the `admins` group.