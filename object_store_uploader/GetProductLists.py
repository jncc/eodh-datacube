import luigi
import os
import logging
import json
import datetime
import glob
import re

log = logging.getLogger('luigi-interface')

#todo: use the CEDA api instead
class GetProductLists(luigi.Task):
    startDate = luigi.DateParameter(default=datetime.date.today())
    endDate = luigi.DateParameter(default=datetime.date.today())
    satellites = luigi.Parameter(default="Sentinel-1A,Sentinel-1B,Sentinel-2A,Sentinel-2B")
    stateLocation = luigi.Parameter()
    ardLocation = luigi.Parameter()

    def hasGenerationTimeInProductName(self, productName):
        pattern = "_T[A-Za-z0-9]+_ORB[0-9]+_\d{14}_"
        return re.search(pattern, productName)

    def isACompleteProduct(self, productName, expectedFiles, allFiles):
        expectedFilesExist = True
        for expectedFile in expectedFiles:
            if expectedFile not in allFiles:
                expectedFilesExist = False
                log.warning(f'Incomplete product files - {expectedFile} is missing, skipping product {productName}')
                break

        return expectedFilesExist

    def getS1Products(self, files):
        products = []
        ignored = []

        dataFileSuffix = '.tif'
        dataFiles = [f for f in files if f.endswith(dataFileSuffix)]

        for dataFile in dataFiles:
            productName = os.path.basename(dataFile).replace(dataFileSuffix, '')

            expectedFiles = [
                dataFile,
                dataFile.replace(dataFileSuffix, '_meta.xml')
            ]

            if self.isACompleteProduct(productName, expectedFiles, files):
                products.append({
                    'productName': productName,
                    'files': expectedFiles
                })
            else:
                ignored.append(productName)

        return products, ignored

    def getS2Products(self, files):
        products = []
        ignored = []

        dataFileSuffix = '_vmsk_sharp_rad_srefdem_stdsref.tif'
        dataFiles = [f for f in files if f.endswith(dataFileSuffix)]

        for dataFile in dataFiles:
            productName = os.path.basename(dataFile).replace(dataFileSuffix, '')

            expectedFiles = [
                dataFile,
                dataFile.replace(dataFileSuffix, '_clouds.tif'),
                dataFile.replace(dataFileSuffix, '_sat.tif'),
                dataFile.replace(dataFileSuffix, '_toposhad.tif'),
                dataFile.replace(dataFileSuffix, '_valid.tif'),
                dataFile.replace('.tif', '_meta.xml'),
                dataFile.replace('.tif', '_thumbnail.jpg')
            ]

            if self.hasGenerationTimeInProductName(productName):
                expectedFiles.append(dataFile.replace(dataFileSuffix, '_clouds_prob.tif'))

            if self.isACompleteProduct(productName, expectedFiles, files):
                products.append({
                    'productName': productName,
                    'files': expectedFiles
                })
            else:
                ignored.append(productName)

        return products, ignored

    def getProducts(self, satelliteCodes):
        products = []
        ignored = []

        for satelliteCode in satelliteCodes:
            datePaths = self.getDatePathsForSatellite(satelliteCode)

            for dateDir in datePaths:
                if os.path.isdir(dateDir):
                    files = glob.glob(os.path.join(dateDir, f'{satelliteCode}*'))

                    if satelliteCode.startswith('S1'):
                        completeProducts, ignoredProducts = self.getS1Products(files)
                        products.extend(completeProducts)
                        ignored.extend(ignoredProducts)
                    else:
                        completeProducts, ignoredProducts = self.getS2Products(files)
                        products.extend(completeProducts)
                        ignored.extend(ignoredProducts)

        return products, ignored

    def getDatePathsForSatellite(self, satelliteCode):
        satelliteType = f'sentinel_{satelliteCode[1]}'

        datePaths = []
        # get all dates between the start and end date
        delta = self.endDate - self.startDate
        for i in range(delta.days + 1):
            day = self.startDate + datetime.timedelta(days=i)
            datePaths.append(os.path.join(self.ardLocation, satelliteType, str(day.year), day.strftime('%m'), day.strftime('%d')))

        return datePaths

    def getSatelliteCodes(self):
        # turn something like Sentinel-1A, Sentinel-1B into S1A, S1B
        return self.satellites.upper().strip(' ').replace('ENTINEL-', '').split(',')

    def run(self):
        satelliteCodes = self.getSatelliteCodes()

        for code in satelliteCodes:
            if code not in ['S1A', 'S1B', 'S2A', 'S2B']:
                raise Exception('Bad satellite option, must choose from: Sentinel-1A, Sentinel-1B, Sentinel-2A, Sentinel-2B')

        completeProducts, ignoredProducts = self.getProducts(satelliteCodes)

        with self.output().open("w") as outFile:
            output = {
                'satelliteCodes': satelliteCodes,
                'products': completeProducts,
                'ignored': ignoredProducts
            }
            outFile.write(json.dumps(output, indent=4, sort_keys=True))
    
    def output(self):
        return luigi.LocalTarget(os.path.join(self.stateLocation, 'GetProductLists.json'))