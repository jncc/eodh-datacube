# JASMIN Object store uploader

Upload ARD from the CEDA archive to the JASMIN object store for use by the datacube. Also generate dataset documents to upload with the ARD files.

## Installation and setup

Create conda env

```
cd object_store_uploader

conda env create -f environment.yaml

conda activate uploader_env
```

## Upload products by date range

Create a configturation file using the `object-store-uploader-luigi.cfg.example` and a object store secrets file using `object-store-secrets.json.example`

Then run from the eodh-datacube level like so:

```
LUIGI_CONFIG_PATH=object_store_uploader/object-store-uploader-luigi.cfg PYTHONPATH='.' luigi --module object_store_uploader CleanupIndexFiles --startDate=2018-09-29 --endDate=2023-04-07 --local-scheduler
```

Or if you don't want to cleanup the index files:
```
LUIGI_CONFIG_PATH=object_store_uploader/object-store-uploader-luigi.cfg PYTHONPATH='.' luigi --module object_store_uploader CheckProducts --startDate=2018-09-29 --endDate=2023-04-07 --local-scheduler
```

You can also use `--testProcessing` if you're running it locally with no access to the actual ARD or object store. The `test` folder is setup with some example files to test against.