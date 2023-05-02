# Object store

To access the UI you'll need to go via an nx-login server using NoMachine. Open a browser and login to your object store tenancy using your JASMIN account portal credentials at a URL formatted like so: http://my-os-tenancy-o.s3.jc.rl.ac.uk/_admin/portal

 > Note that some special characters cause issues on the object store so if you have any problems logging in then reset your JASMIN password to use "safe" special characters, e.g. asterisks (*)

## Setup the object store

Once logged into the object store web console, follow the steps below to set it up for the datacube.

 1. Create the following buckets: `sentinel1-ard` and `sentinel2-ard`
 
 2. Change the bucket policies to allow public read:
 
    1. Select the bucket
    2. Click the settings icon
    3. Click permissions
    4. Uncheck owner only access
    5. Give the policy a name, e.g. `sentinel2-ard-bucket-policy`
    6. Add two statements using the provided templates: `Read-only access for Everyone` and `Full access for Users`
    7. Edit the `Full access for Users` statement to use `Select Users/Groups` and add a group `my-os-tenancy-o-members`

3. Create an access key:

    1. Go back to the object store landing page
    2. Click the settings icon
    3. Click tokens
    4. Add a new token and make sure to check the `S3 Secret Key` option
    5. Save the access key and secret key

4. Upload the Sentinel product specification files [sen1_prod_spec.yaml](sen1_prod_spec.yaml) and [sen2_prod_spec.yaml](sen2_prod_spec.yaml) into their respective buckets.

You'll also need to make sure you have enough storage for the data you want to upload.

> Note 1: The object store can be accessed from the JASMIN external cloud (but not the wider Internet). You'll need to use the `s3-ext` version of the URL and include the domain explicitly as a query string parameter to do this, e.g. `http://my-os-tenancy-o.s3-ext.jc.rl.ac.uk/sentinel2-ard/2019/06/27/S2A_20190627_lat50lon544_T29UQR_ORB080_utm29n_osgb_vmsk_sharp_rad_srefdem_stdsref.tif?domain=my-os-tenancy-o.s3-ext.jc.rl.ac.uk`

> Note 2: There doesn't seem to be a way to set up programmatic keys, i.e. ones not tied to a user account.

## Setup the object_store_uploader scripts

These scripts are run on a JASMIN sci server so you'll need to save them to a group workspace or your home directory.

1. Login to a JASMIN sci server

2. Install mamba to your persistent storage area following their instructions [here](https://mamba.readthedocs.io/en/latest/installation.html)

3. Clone this repo

        cd <your_working_area>
        git clone https://github.com/jncc/eodh-datacube.git
        cd eodh-datacube/object_store_uploader

4. Follow the setup instructions in [object_store_uploader/README.md](../object_store_uploader/README.md) to create the mamba environment

5. Create a `scripts`, `config`, `state`, and `working` folder, e.g.

        mkdir <your_working_area>/scripts <your_working_area>/config <your_working_area>/state <your_working_area>/working

6. Add a `object-store-uploader-luigi.cfg` and `object-store-secrets.json` file to `<your_working_area>/config` using the examples [object-store-uploader-luigi.cfg.example](../object_store_uploader/object-store-uploader-luigi.cfg.example) and [object-store-secrets.json.example](../object_store_uploader/object-store-secrets.json.example).

    > Note the `ardLocation` in this case would be `/neodc/sentinel_ard/data`

7. Create a helper script called `upload_s2_products_to_object_store_between_dates.sh` in your `<your_working_area>/scripts` folder with contents like so:

        #!/bin/bash
        # Dates in 2023-01-31 format

        START_DATE=$1
        END_DATE=$2
        SATELLITES="Sentinel-2A,Sentinel-2B"

        # Create dir to put state files in
        batchName="${START_DATE}_${END_DATE}_$(date +%Y%m%d%H%M%S)"
        stateDir="<your_working_area>/state/$batchName"
        workingDir="<your_working_area>/working/$batchName"
        mkdir -p $stateDir
        mkdir -p $workingDir

        export PATH=<your_conda_install>/bin:$PATH
        source activate uploader_env

        LUIGI_CONFIG_PATH='<your_working_area>/config/object-store-uploader-luigi.cfg' PYTHONPATH='/<your_working_area>/eodh-datacube' luigi --module object_store_uploader CleanupIndexFiles --startDate=$START_DATE --endDate=$END_DATE --satellites=$SATELLITES --stateLocation=$stateDir --workingLocation=$workingDir --local-scheduler

    > Make sure you substitute the `<your_working_area>` and `<your_conda_install>` paths

8. Make it an executable

        chmod +x <your_working_area>/scripts/upload_s2_products_to_object_store_between_dates.sh

9. You can then either call it directly on the sci server like so:

        <your_working_area>/scripts/upload_s2_products_to_object_store_between_dates.sh 2023-01-01 2023-01-31

    Or run it as a LOTUS job:

        sbatch -p short-serial --time 24:00:00 -o %J.out -e %J.err <your_working_area>/scripts/upload_s2_products_to_object_store_between_dates.sh 2023-01-01 2023-01-31

    > Upload times will vary depending on the number of products in a batch. Generally speaking a month of Sentinel-2 will take less than 24 hours to upload.

    > Since this isn't going out to the Internet, the JASMIN xfer servers probably aren't helpful here.
