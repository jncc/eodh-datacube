import luigi
import os
import logging
import json

from luigi.util import requires
from object_store_uploader.CheckProducts import CheckProducts

log = logging.getLogger('luigi-interface')

@requires(CheckProducts)
class CleanupIndexFiles(luigi.Task):
    stateLocation = luigi.Parameter()
    workingLocation = luigi.Parameter()

    def run(self):
        log.info('Cleaning up all files in working folder')
        filenames = os.listdir(self.workingLocation)
        filePaths = []
        for filename in filenames:
            filePath = os.path.join(self.workingLocation, filename)
            os.remove(filePath)
            filePaths.append(filePath)

        with self.output().open("w") as outFile:
            output = {
                'files' : filePaths
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))
    
    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, 'CleanupIndexFiles.json'))