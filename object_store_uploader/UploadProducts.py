import luigi
import os
import logging
import json
from luigi.util import requires
from object_store_uploader.GenerateDatacubeIndexFiles import GenerateDatacubeIndexFiles
from object_store_uploader.UploadProductFiles import UploadProductFiles

log = logging.getLogger('luigi-interface')


@requires(GenerateDatacubeIndexFiles)
class UploadProducts(luigi.Task):
    stateLocation = luigi.Parameter()
    credentialsFilePath = luigi.Parameter()
    s1BucketName = luigi.Parameter()
    s2BucketName = luigi.Parameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        products = []
        with self.input().open('r') as getProductLists:
            getProductListsInfo = json.load(getProductLists)
            products = getProductListsInfo['products']

        tasks = []
        for product in products:
            productName = product['productName']
            bucket = ''
            if productName.startswith('S1'):
                bucket = self.s1BucketName
            elif productName.startswith('S2'):
                bucket = self.s2BucketName

            year = productName[4:8]
            month = productName[8:10]
            date = productName[10:12]

            objectStoreProductBasePath = os.path.join(bucket, year, month, date)

            tasks.append(UploadProductFiles(
                stateLocation=self.stateLocation,
                product=product,
                objectStoreBasePath=objectStoreProductBasePath,
                credentialsFilePath=self.credentialsFilePath,
                testProcessing=self.testProcessing
            ))

        yield tasks

        objectStoreProducts = []
        for task in tasks:
            with task.output().open('r') as output:
                objectStoreProducts.append(json.load(output))

        with self.output().open("w") as outFile:
            output = {
                'products': objectStoreProducts
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, 'UploadProducts.json'))
