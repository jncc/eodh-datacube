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

DATA_FILE_SUFFIX = '_vmsk_sharp_rad_srefdem_stdsref.tif'

class GenerateS2IndexFile(luigi.Task):
    product = luigi.DictParameter()
    indexFilePath = luigi.Parameter()
    objectStoreBaseUrl = luigi.Parameter()
    objectStoreUrlParams = luigi.Parameter()
    s2BucketName = luigi.Parameter()
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
        dataFilePath = self.getProductFile(self.product, DATA_FILE_SUFFIX)
        dataFilename = os.path.basename(dataFilePath)
        metadataFilePath = self.getProductFile(self.product, '_meta.xml')
        fmaskFilePath = self.getProductFile(self.product, '_clouds.tif')
        vmaskFilePath = self.getProductFile(self.product, '_valid.tif')
        topomaskFilePath = self.getProductFile(self.product, '_toposhad.tif')

        year = productName[4:8]
        month = productName[8:10]
        day = productName[10:12]
        urlPrefix = '{0}/{1}/{2}/{3}/{4}/'.format(self.objectStoreBaseUrl, self.s2BucketName, year, month, day)
        dataFileUrl = urljoin(urlPrefix, urljoin(dataFilename, self.objectStoreUrlParams))
        fmaskFileUrl = urljoin(urlPrefix, urljoin(os.path.basename(fmaskFilePath), self.objectStoreUrlParams))
        vmaskFileUrl = urljoin(urlPrefix, urljoin(os.path.basename(vmaskFilePath), self.objectStoreUrlParams))
        topomaskFileUrl = urljoin(urlPrefix, urljoin(os.path.basename(topomaskFilePath), self.objectStoreUrlParams))

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
        image_lyrs['blue'] = {'layer': 1, 'path': dataFileUrl}
        image_lyrs['green'] = {'layer': 2, 'path': dataFileUrl}
        image_lyrs['red'] = {'layer': 3, 'path': dataFileUrl}
        image_lyrs['rededge1'] = {'layer': 4, 'path': dataFileUrl}
        image_lyrs['rededge2'] = {'layer': 5, 'path': dataFileUrl}
        image_lyrs['rededge3'] = {'layer': 6, 'path': dataFileUrl}
        image_lyrs['nir1'] = {'layer': 7, 'path': dataFileUrl}
        image_lyrs['nir2'] = {'layer': 8, 'path': dataFileUrl}
        image_lyrs['swir1'] = {'layer': 9, 'path': dataFileUrl}
        image_lyrs['swir2'] = {'layer': 10, 'path': dataFileUrl}
        image_lyrs['fmask'] = {'layer': 1, 'path': fmaskFileUrl}
        image_lyrs['vmask'] = {'layer': 1, 'path': vmaskFileUrl}
        image_lyrs['topomask'] = {'layer': 1, 'path': topomaskFileUrl}

        if not self.testProcessing:
            epsgCode = rsgislib.imageutils.get_epsg_proj_from_img(dataFilePath)
            boundingBox = rsgislib.imageutils.get_img_bbox(dataFilePath)
        else:
            epsgCode = '27700'
            boundingBox = ['0.0','0.0','0.0','0.0']

        scn_info = {
            'id': str(uuid.uuid4()),
            'processing_level': 'LEVEL_2',
            'product_type': 'ARCSI_SREF',
            'creation_dt': str(creationDate),
            'label': productName,
            'platform': {'code': 'SENTINEL-2'},
            'instrument': {'name': 'MSI'},
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