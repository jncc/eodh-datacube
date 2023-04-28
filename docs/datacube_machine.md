# Datacube machine

## Setup

### Create a machine in the JASMIN cloud portal

1. Login using your JASMIN user credentials and navigate to your external cloud tenancy
2. Create a new machine under the Machines tab:
    * Name: `datacube`
    * Image: `ubuntu-2004-20221013`
    * Size: `j4.large`
3. Create a new volume under the Volumes tab:
    * Name: `datacube-vol`
    * Size (GB): `40`
4. Attach the volume to the `datacube` machine

The root user for the machine will use the same ssh key as your JASMIN cloud portal user so you'll need to use this to login until it's configured with FreeIPA.

### Login

1. ssh to a machine with an external IP using your JASMIN cloud portal username and key and authentication forwarding

        ssh -A <username>@<external_ip>


2. ssh to the `datacube` machine

        ssh root@<datacube_ip>

### Configure a FreeIPA client

For first time server setup, you can follow [this guide](https://computingforgeeks.com/how-to-configure-freeipa-client-on-ubuntu-centos/) to configure the FreeIPA client. E.g.:

1. Install the freeipa-client package

        sudo apt-get update
        sudo apt-get -y upgrade
        sudo apt-get install freeipa-client

    Enter to skip through input fields

2. Edit the `/etc/hosts` file to add this entry:

        <freeipa_ip> <freeipa_name>.novalocal ipa

    Where \<freeipa_ip> is the internal IP of the FreeIPA machine created by the identity manager cluster, and \<freeipa_name> is the name, e.g. `identity-freeipa-0`.

3. Run the client install command, subbing in the <freeipa_name> where needed:

        ipa-client-install --hostname=`hostname -f` --mkhomedir --server=<freeipa_name>.novalocal --domain <freeipa_name>.novalocal

    Use the following options:
    * Proceed with fixed values and no DNS discovery: yes
    * Continue to configure with these values: yes
    * Admin username and password: use the FreeIPA admin credentials

4. Run the following command to configure the user home directories:

        sudo bash -c "cat > /usr/share/pam-configs/mkhomedir" <<EOF
        Name: activate mkhomedir
        Default: yes
        Priority: 900
        Session-Type: Additional
        Session:
        required pam_mkhomedir.so umask=0022 skel=/etc/skel
        EOF

        sudo pam-auth-update
    
    Enter to proceed with defaults

5. Log out of root and login as the FreeIPA admin user to check FreeIPA has been configured correctly

6. Configure sudo for all users in the FreeIPA admin group

    First initialise the session using the FreeIPA admin credentials

        kinit admin

    Then set up a group with all sudorules

        ipa sudorule-add --cmdcat=all All
        ipa sudorule-add-user --groups=admins All

    Then edit the `/etc/nsswitch.conf` file so that the sudoers list includes ldap like so

        sudoers: files sss ldap

### Configure and mount the volume at /data

By following the JASMIN guide: https://help.jasmin.ac.uk/article/285-system-administration-guidance-for-the-unmanaged-cloud

### Set up a cube-in-a-box

Pull down the git repo and run their setup script which will install make, docker, and docker-compose, then start the docker service.

    cd /data
    git clone https://github.com/opendatacube/cube-in-a-box
    cd cube-in-a-box
    bash setup.sh
    sudo systemctl start docker

Log out then in again, then spin up the docker containers and initialise the database.

    cd /data/cube-in-a-box
    make up-prod
    make init

At this point you have a "jupyter" container with jupyter notebook and the datacube cli, and a "postgres" container with an initialised but empty db. You can use the datacube cli like so:

    docker-compose exec jupyter datacube --version