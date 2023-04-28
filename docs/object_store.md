# Object store

To access the UI you'll need to go via an nx-login server using NoMachine. Open a browser and login to your object store tenancy using your JASMIN account portal credentials at a URL formatted like so: http://my-os-tenancy-o.s3.jc.rl.ac.uk/_admin/portal

 > Note that some special characters cause issues on the object store so if you have any problems logging in then reset your JASMIN password to use "safe" special characters, e.g. asterisks (*)

## Setup

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