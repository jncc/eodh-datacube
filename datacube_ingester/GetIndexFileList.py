import luigi
import os
import logging
import json
import datetime
import s3fs
import re

log = logging.getLogger('luigi-interface')


class GetIndexFileList(luigi.Task):
    startDate = luigi.DateParameter(default=datetime.date.today())
    endDate = luigi.DateParameter(default=datetime.date.today())
    stateLocation = luigi.Parameter()
    s1BucketName = luigi.Parameter()
    s2BucketName = luigi.Parameter()
    credentialsFilePath = luigi.Parameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        allProducts = []

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

                allProducts += jasmin_s3.glob(f'{self.s1BucketName}/*/*/*/S1*.yaml')
                allProducts += jasmin_s3.glob(f'{self.s2BucketName}/*/*/*/S2*.yaml')
        else:
            logging.info('Test mode: using testFiles.json instead of querying the object store')
            with open('datacube_ingester/test/testFiles.json', 'r') as f:
                testFiles = json.load(f)
                allProducts = testFiles['indexFiles']

        indexFiles = []
        delta = self.endDate - self.startDate
        for i in range(delta.days + 1):
            date = self.startDate + datetime.timedelta(days=i)
            pattern = re.compile('sentinel[12]-ard/{0}/{1}/{2}/S[12][a-zA-Z0-9_]+.yaml'.format(str(date.year), date.strftime('%m'), date.strftime('%d')))
            indexFiles += filter(pattern.match, allProducts)

        with self.output().open("w") as outFile:
            output = {
                'indexFiles': indexFiles
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, 'GetIndexFileList.json'))
