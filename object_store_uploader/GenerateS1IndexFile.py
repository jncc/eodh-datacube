import luigi
import os
import logging
import yaml
import uuid
import xml.etree.ElementTree as ET
import rsgislib.imageutils
from urllib.parse import urljoin
from datetime import datetime

log = logging.getLogger('luigi-interface')


class GenerateS1IndexFile(luigi.Task):
    product = luigi.DictParameter()
    indexFilePath = luigi.Parameter()
    objectStoreBaseUrl = luigi.Parameter()
    objectStoreUrlParams = luigi.Parameter()
    s1BucketName = luigi.Parameter()
    testProcessing = luigi.BoolParameter()

    def getProductFile(self, product, ending):
        file = ''

        for productFile in product['files']:
            if productFile.endswith(ending):
                file = productFile
                break

        if not file:
            raise Exception(f'Something went wrong, could not find file with ending {ending} for product {product["productName"]}')

        return file

    def run(self):
        productName = self.product['productName']
        dataFilePath = self.getProductFile(self.product, '.tif')
        dataFilename = os.path.basename(dataFilePath)
        metadataFilePath = self.getProductFile(self.product, '_meta.xml')

        year = productName[4:8]
        month = productName[8:10]
        day = productName[10:12]
        urlPrefix = '{0}/{1}/{2}/{3}/{4}/'.format(self.objectStoreBaseUrl, self.s1BucketName, year, month, day)
        dataFileUrl = urljoin(urlPrefix, urljoin(dataFilename, self.objectStoreUrlParams))

        prefixMap = {
            'gmd': 'http://www.isotc211.org/2005/gmd',
            'gml': 'http://www.opengis.net/gml'
        }
        root = ET.parse(metadataFilePath).getroot()

        creationDate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        startDate = datetime.strptime(root.find('.//gml:beginPosition', prefixMap).text, '%Y-%m-%dT%H:%M:%SZ')
        endDate = datetime.strptime(root.find('.//gml:endPosition', prefixMap).text, '%Y-%m-%dT%H:%M:%SZ')
        centerDate = (startDate + (endDate - startDate)/2).strftime('%Y-%m-%d %H:%M:%S')
        westboundLon = float(root.find('.//gmd:westBoundLongitude', prefixMap)[0].text)
        eastboundLon = float(root.find('.//gmd:eastBoundLongitude', prefixMap)[0].text)
        southboundLat = float(root.find('.//gmd:southBoundLatitude', prefixMap)[0].text)
        northboundLat = float(root.find('.//gmd:northBoundLatitude', prefixMap)[0].text)

        image_lyrs = dict()
        image_lyrs['vv'] = {'layer': 1, 'path': dataFileUrl}
        image_lyrs['vh'] = {'layer': 2, 'path': dataFileUrl}

        if not self.testProcessing:
            epsgCode = rsgislib.imageutils.get_epsg_proj_from_img(dataFilePath)
            boundingBox = rsgislib.imageutils.get_img_bbox(dataFilePath)
        else:
            epsgCode = '27700'
            boundingBox = ['0.0', '0.0', '0.0', '0.0']

        scn_info = {
            'id': str(uuid.uuid4()),
            'product_type': 'gamma_0',
            'creation_dt': str(creationDate),
            'label': productName,
            'platform': {'code': 'SENTINEL-1'},
            'instrument': {'name': 'SAR'},
            'extent': {
                'from_dt': str(startDate),
                'to_dt': str(endDate),
                'center_dt': centerDate,
                'coord': {
                    'll': {'lat': southboundLat, 'lon': westboundLon},
                    'lr': {'lat': southboundLat, 'lon': eastboundLon},
                    'ul': {'lat': northboundLat, 'lon': westboundLon},
                    'ur': {'lat': northboundLat, 'lon': eastboundLon}
                }
            },
            'format': {'name': 'GTIFF'},
            'grid_spatial': {
                'projection': {
                    'spatial_reference': f'EPSG:{epsgCode}',
                    'geo_ref_points': {
                        'll': {'x': boundingBox[0], 'y': boundingBox[2]},
                        'lr': {'x': boundingBox[1], 'y': boundingBox[2]},
                        'ul': {'x': boundingBox[0], 'y': boundingBox[3]},
                        'ur': {'x': boundingBox[1], 'y': boundingBox[3]}
                    }
                }
            },
            'image': {'bands': image_lyrs},
            'lineage': {'source_datasets': {}},
        }

        with open(self.indexFilePath, 'w') as stream:
            yaml.dump(scn_info, stream)

    def output(self):
        return luigi.LocalTarget(self.indexFilePath)
