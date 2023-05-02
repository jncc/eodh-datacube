# Pangeo cluster

## Setup

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

    > Cluster creation takes ~20 mins

5. Once the cluster has been created, try spawning a container by going to `https://pangeo.<your-hyphenated-external-ip>.sslip.io/` and logging in with your FreeIPA user
6. Allow for the saving of larger notebooks by increasing the `message body size` setting in nginx:
    
    1. Login to the kubernetes dashboard at `https://dashboard.<your-hyphenated-external-ip>.sslip.io/`
    2. Change `Namespace` to `nginx-ingress`
    3. Under `Config and Storage` click on `Config Maps` then `nginx-ingress-ingress-nginx-controller`
    4. Click the edit icon and add a `proxy-body-size` value under `data`, e.g.:

            data:
                proxy-body-size: 500m
                proxy-buffer-size: 64k
    5. Click `Update`

## New user configuration

A few things need setting up for a user to be able to access the datacube.

1. Create a new user in FreeIPA and login to a Jupyterhub session using their temporary credentials.
2. Add a `.datacube.conf` file to the persistent storage area. You can use the same file as the one stored in `/data/config` on the datacube machine.
3. Setup a mamba/conda env in the persistent storage area in which to install the datacube by running the following commands in a terminal (I'd recommend saving these in a script):

        cd ~

        # Install mamba
        wget "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh"
        bash Mambaforge-Linux-x86_64.sh -b

        # Create datacube env
        conda env export -f env.yaml
        source mambaforge/bin/activate
        mamba create -n datacube
        mamba env update -n datacube -f env.yaml
        conda install -n datacube -y datacube

        # Initialise datacube env to be startup env
        mamba init
        mv ~/.bashrc ~/.profile
        echo "mamba activate datacube" >> ~/.profile
        echo "/home/jovyan/mambaforge/envs/datacube" > ~/.conda/environments.txt

        # Cleanup
        rm Mambaforge-Linux-x86_64.sh
        rm env.yaml

    > Note: ideally the datacube install would come as part of the container but this works for now

4. Restart the server, create a new notebook that uses the `conda env:datacube` kernel and run the following commands:

        import datacube
        dc = datacube.Datacube()

        query = {
            'time': ('2020-01-01','2020-12-31'),
            'output_crs': 'epsg:27700',
            'resolution': (-10,10)
        }

        ds = dc.load(product='sentinel2',
                    dask_chunks={},
                    **query)
        ds

    The commands should execute successfully and return an xarray dataset. If not, something has failed with the setup.

5. Cleanup by deleting the notebook that you created and running this command in the terminal to clear the command history:

        history -c

6. Shut down the server and logout. It should be ready for the user to use at this point.