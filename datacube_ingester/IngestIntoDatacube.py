import luigi
import os
import logging
import json
import subprocess
from luigi.util import requires
from datacube_ingester.DownloadIndexFiles import DownloadIndexFiles

log = logging.getLogger('luigi-interface')


@requires(DownloadIndexFiles)
class IngestIntoDatacube(luigi.Task):
    stateLocation = luigi.Parameter()
    cleanupFiles = luigi.BoolParameter(default=False)
    testProcessing = luigi.BoolParameter()

    def run(self):
        files = {}
        with self.input().open('r') as getDownloadIndexFiles:
            files = json.load(getDownloadIndexFiles)['files']

        if not self.testProcessing:
            for file in files:
                cmd = f'datacube dataset add {file}'
                log.info(f'Running command: {cmd}')
                subprocess.run(cmd, shell=True, check=True)

        if self.cleanupFiles:
            log.info('Cleaning up index files')
            for file in files:
                os.remove(file)

        with self.output().open("w") as outFile:
            output = {
                'filesIngested': files
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, 'IngestIntoDatacube.json'))
