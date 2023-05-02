import luigi
import os
import logging
import json
from luigi.util import requires
from object_store_uploader.GetProductLists import GetProductLists
from object_store_uploader.GenerateS1IndexFile import GenerateS1IndexFile
from object_store_uploader.GenerateS2IndexFile import GenerateS2IndexFile

log = logging.getLogger('luigi-interface')


@requires(GetProductLists)
class GenerateDatacubeIndexFiles(luigi.Task):
    stateLocation = luigi.Parameter()
    workingLocation = luigi.Parameter()
    objectStoreBaseUrl = luigi.Parameter()
    objectStoreUrlParams = luigi.Parameter()
    s1BucketName = luigi.Parameter()
    s2BucketName = luigi.Parameter()
    testProcessing = luigi.BoolParameter()

    def run(self):
        products = {}
        with self.input().open('r') as getProductLists:
            getProductListsInfo = json.load(getProductLists)
            products = getProductListsInfo

        tasks = []

        productsWithIndexFiles = []
        for product in products['products']:
            productName = product['productName']
            indexFilePath = os.path.join(self.workingLocation, f'{productName}.yaml')
            productWithIndexFile = {
                'productName': productName,
                'files': product['files']
            }
            productWithIndexFile['files'].append(indexFilePath)
            productsWithIndexFiles.append(productWithIndexFile)

            if productName.startswith('S1'):
                tasks.append(GenerateS1IndexFile(
                    product=product,
                    indexFilePath=indexFilePath,
                    objectStoreBaseUrl=self.objectStoreBaseUrl,
                    objectStoreUrlParams=self.objectStoreUrlParams,
                    s1BucketName=self.s1BucketName,
                    testProcessing=self.testProcessing
                ))
            else:
                tasks.append(GenerateS2IndexFile(
                    product=product,
                    indexFilePath=indexFilePath,
                    objectStoreBaseUrl=self.objectStoreBaseUrl,
                    objectStoreUrlParams=self.objectStoreUrlParams,
                    s2BucketName=self.s2BucketName,
                    testProcessing=self.testProcessing
                ))

        yield tasks

        with self.output().open("w") as outFile:
            output = {
                'products': productsWithIndexFiles
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, 'GenerateDatacubeIndexFiles.json'))
