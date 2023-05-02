import luigi
import os
import logging
import json
import s3fs
from luigi.util import requires
from datacube_ingester.GetIndexFileList import GetIndexFileList

log = logging.getLogger('luigi-interface')


@requires(GetIndexFileList)
class DownloadIndexFiles(luigi.Task):
    stateLocation = luigi.Parameter()
    workingLocation = luigi.Parameter()
    credentialsFilePath = luigi.Parameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        fileList = {}
        with self.input().open('r') as getIndexFileList:
            fileList = json.load(getIndexFileList)['indexFiles']

        downloadedFiles = []
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

                for file in fileList:
                    filename = os.path.basename(file)
                    filePath = os.path.join(self.workingLocation, filename)
                    jasmin_s3.get(file, filePath)
                    downloadedFiles.append(filePath)
        else:
            logging.info('Test mode: creating test files instead of downloading')
            for file in fileList:
                filename = os.path.basename(file)
                testFilePath = os.path.join(self.workingLocation, filename)

                with open(testFilePath, 'w') as testFile:
                    testFile.write('TEST')

                downloadedFiles.append(testFilePath)


        with self.output().open('w') as outFile:
            output = {
                'files': downloadedFiles
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, 'DownloadIndexFiles.json'))
