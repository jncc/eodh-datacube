# Pangeo cluster

Create a new pangeo cluster in the [JASMIN cloud portal](https://cloud.jasmin.ac.uk/):

1. Login using your JASMIN user credentials and navigate to your external cloud tenancy
2. Click the clusters tab once it appears
3. Click the new cluster button
4. Pick the pangeo cluster type and provide it with:

    * Cluster name: `pangeo`
    * Identity manager: `identity`
    * Version: `1.24`
    * Worker nodes: `4`
    * Master size: `j3.medium`
    * Worker size: `j4.large`
    * Root volume size (GB): `40`
    * External IP: `(pick one of the available options)`
    * Admin IP ranges: `(provide an IP range)`
    * Dashboard domain: `(empty)`
    * Notebook CPUs: `4`
    * Notebook RAM (GB): `28`
    * Notebook storage (GB): `100`
    * Pangeo domain: `(empty)`

Cluster creation takes around 20 minutes. Once created, you can login to the FreeIPA interface with the admin user at `https://<your-hyphenated-external-ip>.sslip.io/`. (If you get a login pop up from your browser, cancel it.)

