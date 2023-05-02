import luigi
import os
import logging
import json
import s3fs

log = logging.getLogger('luigi-interface')


class UploadProductFiles(luigi.Task):
    stateLocation = luigi.Parameter()
    product = luigi.DictParameter()
    objectStoreBasePath = luigi.Parameter()
    credentialsFilePath = luigi.Parameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        objectStoreFiles = []
        if not self.testProcessing:
            with open(self.credentialsFilePath) as f:
                jasmin_store_credentials = json.load(f)

                jasmin_s3 = s3fs.S3FileSystem(
                    anon=False,
                    secret=jasmin_store_credentials['secret'],
                    key=jasmin_store_credentials['token'],
                    client_kwargs={
                        'endpoint_url': jasmin_store_credentials['endpoint_url']
                        })

                for file in self.product['files']:
                    objectStoreFilePath = '{0}/{1}'.format(self.objectStoreBasePath, os.path.basename(file))

                    log.info(f'Copying {file} to {objectStoreFilePath}')
                    jasmin_s3.put(file, objectStoreFilePath)

                    objectStoreFiles.append(objectStoreFilePath)

        else:
            for file in self.product['files']:
                objectStoreFilePath = '{0}/{1}'.format(self.objectStoreBasePath, os.path.basename(file))

                log.info(f'Copying {file} to {objectStoreFilePath} (not really - test mode)')

                objectStoreFiles.append(objectStoreFilePath)

        with self.output().open("w") as outFile:
            output = {
                'productName': self.product['productName'],
                'files': objectStoreFiles
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, f'UploadProductFiles_{self.product["productName"]}.json'))
