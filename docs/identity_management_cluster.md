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
    * Admin IP ranges: `0.0.0.0/0`
    * FreeIPA size: `j3.small`
    * Keycloak size: `j3.small`
    * Gateway size: `j3.small`
    * Gateway domain: `(empty)`

Cluster creation takes around 20 minutes. Once created, you can login to the FreeIPA interface with the admin user at `https://<your-hyphenated-external-ip>.sslip.io/`. (If you get a login pop up from your browser, cancel it.)

## Adding a user

