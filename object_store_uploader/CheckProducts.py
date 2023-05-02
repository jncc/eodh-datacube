import luigi
import os
import logging
import json

from luigi.util import requires
from object_store_uploader.CheckProductFiles import CheckProductFiles
from object_store_uploader.UploadProducts import UploadProducts

log = logging.getLogger('luigi-interface')


@requires(UploadProducts)
class CheckProducts(luigi.Task):
    stateLocation = luigi.Parameter()
    credentialsFilePath = luigi.Parameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        products = []
        with self.input().open('r') as getProductLists:
            products = json.load(getProductLists)['products']

        tasks = []
        for product in products:
            tasks.append(CheckProductFiles(
                stateLocation=self.stateLocation,
                product=product,
                credentialsFilePath=self.credentialsFilePath,
                testProcessing=self.testProcessing
            ))

        yield tasks

        with self.output().open("w") as outFile:
            output = {
                'products': products
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, 'CheckProducts.json'))
