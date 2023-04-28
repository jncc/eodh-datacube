# JASMIN datacube ingester

Download index files from the JASMIN object store and ingest them into the datacube. To be run locally on the datacube VM.

## Installation and setup

Create conda/mamba env (the datacube install is much faster with mamba)

```
mamba create -n datacube_ingester python=3.10
mamba activate datacube_ingester
pip install -r requirements.txt
mamba install -y datacube -c conda-forge
```

## Ingest products by date range

Create a configuration file using the `datacube-ingester-luigi.cfg.example` and a object store secrets file using `object-store-secrets.json.example`

Then run from the eodh-datacube level like so:

```
LUIGI_CONFIG_PATH=datacube_ingester/datacube-ingester-luigi.cfg PYTHONPATH='.' luigi --module datacube_ingester IngestIntoDatacube --startDate=2019-01-01 --endDate=2020-12-31 --local-scheduler
```

You can also use `--testProcessing` if you're running it locally with no access to object store or datacube. The `test` folder is setup with a testFiles.json containing a file list to test with.