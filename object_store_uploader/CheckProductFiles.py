import luigi
import os
import logging
import json
import s3fs

log = logging.getLogger('luigi-interface')


class CheckProductFiles(luigi.Task):
    stateLocation = luigi.Parameter()
    product = luigi.DictParameter()
    credentialsFilePath = luigi.Parameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        missingFiles = []

        if not self.testProcessing:
            with open(self.credentialsFilePath) as f:
                jasmin_store_credentials = json.load(f)

                jasmin_s3 = s3fs.S3FileSystem(
                    anon=False,
                    secret=jasmin_store_credentials['secret'],
                    key=jasmin_store_credentials['token'],
                    client_kwargs={'endpoint_url': jasmin_store_credentials['endpoint_url']
                                   })

                for osFile in self.product['files']:
                    if not jasmin_s3.exists(osFile):
                        missingFiles.append(osFile)

        if len(missingFiles) > 0:
            raise Exception(f'Something went wrong - could not find the following files in the object store: {missingFiles}')

        with self.output().open("w") as outFile:
            output = {
                'files': self.product['files']
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, f'CheckProductFiles_{self.product["productName"]}.json'))
