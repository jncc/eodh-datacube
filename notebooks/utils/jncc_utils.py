# adapted / taken drom DEA tool scripts
import geopandas as gpd
import matplotlib as mpl
import matplotlib.cm as cm
from matplotlib import colors as mcolours
import matplotlib.patheffects as PathEffects
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
from pyproj import Proj, transform
from IPython.display import display
from matplotlib.colors import ListedColormap
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from mpl_toolkits.axes_grid1 import make_axes_locatable
from ipyleaflet import Map, Marker, Popup, GeoJSON, basemaps, Choropleth
from skimage import exposure
from matplotlib.animation import FuncAnimation
import pandas as pd
from pathlib import Path
from shapely.geometry import box
from skimage.exposure import rescale_intensity
from tqdm.auto import tqdm
import warnings
import collections
import numpy as np
import xarray as xr
import rasterio.features
import scipy.interpolate
from scipy import ndimage as nd
from skimage.measure import label
from skimage.measure import find_contours
from shapely.geometry import LineString, MultiLineString, shape
from datacube.utils.geometry import CRS, Geometry
from scipy import stats
from scipy.ndimage import grey_dilation, grey_erosion
from scipy.ndimage.filters import uniform_filter
from scipy.ndimage.measurements import variance
from skimage.morphology import disk
#import hdmedians as hd
'''
Note on sources of functions. Unless otherwise stated. They have been taken from GeoscienceAustralia on a Apache License 2.0 license. Please see more details:
https://www.apache.org/licenses/LICENSE-2.0

def rgb and def image_shape has been adapted from:
https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Tools/dea_tools/plotting.py

def xr_vectorize and def xr_rasterize has been directly taken from
https://github.com/GeoscienceAustralia/dea-notebooks/blob/916db231dcb3698e57b0b2c53b6c751f2ab40e06/Scripts/dea_spatialtools.py

def filter_s1, def filter_S2_small and def filter_S2_large are specifically written for JNCC


'''


def xr_vectorize(da, 
                 attribute_col='attribute', 
                 transform=None, 
                 crs=None, 
                 dtype='float32',
                 export_shp=False,
                 **rasterio_kwargs):    
    """
    Vectorises a xarray.DataArray into a geopandas.GeoDataFrame.
    
    Parameters
    ----------
    da : xarray dataarray or a numpy ndarray  
    attribute_col : str, optional
        Name of the attribute column in the resulting geodataframe. 
        Values of the raster object converted to polygons will be 
        assigned to this column. Defaults to 'attribute'.
    transform : affine.Affine object, optional
        An affine.Affine object (e.g. `from affine import Affine; 
        Affine(30.0, 0.0, 548040.0, 0.0, -30.0, "6886890.0) giving the 
        affine transformation used to convert raster coordinates 
        (e.g. [0, 0]) to geographic coordinates. If none is provided, 
        the function will attempt to obtain an affine transformation 
        from the xarray object (e.g. either at `da.transform` or
        `da.geobox.transform`).
    crs : str or CRS object, optional
        An EPSG string giving the coordinate system of the array 
        (e.g. 'EPSG:3577'). If none is provided, the function will 
        attempt to extract a CRS from the xarray object's `crs` 
        attribute.
    dtype : str, optional
         Data type must be one of int16, int32, uint8, uint16, 
         or float32
    export_shp : Boolean or string path, optional
        To export the output vectorised features to a shapefile, supply
        an output path (e.g. 'output_dir/output.shp'. The default is 
        False, which will not write out a shapefile. 
    **rasterio_kwargs : 
        A set of keyword arguments to rasterio.features.shapes
        Can include `mask` and `connectivity`.
    
    Returns
    -------
    gdf : Geopandas GeoDataFrame
    
    """

    
    # Check for a crs object
    try:
        crs = da.crs
    except:
        if crs is None:
            raise Exception("Please add a `crs` attribute to the "
                            "xarray.DataArray, or provide a CRS using the "
                            "function's `crs` parameter (e.g. 'EPSG:3577')")
            
    # Check if transform is provided as a xarray.DataArray method.
    # If not, require supplied Affine
    if transform is None:
        try:
            # First, try to take transform info from geobox
            transform = da.geobox.transform
        # If no geobox
        except:
            try:
                # Try getting transform from 'transform' attribute
                transform = da.transform
            except:
                # If neither of those options work, raise an exception telling the 
                # user to provide a transform
                raise Exception("Please provide an Affine transform object using the "
                        "`transform` parameter (e.g. `from affine import "
                        "Affine; Affine(30.0, 0.0, 548040.0, 0.0, -30.0, "
                        "6886890.0)`")
    
    # Check to see if the input is a numpy array
    if type(da) is np.ndarray:
        vectors = rasterio.features.shapes(source=da.astype(dtype),
                                           transform=transform,
                                           **rasterio_kwargs)
    
    else:
        # Run the vectorizing function
        vectors = rasterio.features.shapes(source=da.data.astype(dtype),
                                           transform=transform,
                                           **rasterio_kwargs)
    
    # Convert the generator into a list
    vectors = list(vectors)
    
    # Extract the polygon coordinates and values from the list
    polygons = [polygon for polygon, value in vectors]
    values = [value for polygon, value in vectors]
    
    # Convert polygon coordinates into polygon shapes
    polygons = [shape(polygon) for polygon in polygons]
    
    # Create a geopandas dataframe populated with the polygon shapes
    gdf = gpd.GeoDataFrame(data={attribute_col: values},
                           geometry=polygons,
                           crs={'init': str(crs)})
    
    # If a file path is supplied, export a shapefile
    if export_shp:
        gdf.to_file(export_shp) 
        
    return gdf



def image_shape(d):
    """Returns (Height, Width) of a given dataset/datarray"""
    dim_names = (("y", "x"), ("latitude", "longitude"))

    dims = set(d.dims)
    h, w = None, None
    for n1, n2 in dim_names:
        if n1 in dims and n2 in dims:
            h, w = (d.coords[n].shape[0] for n in (n1, n2))
            break

    if h is None:
        raise ValueError(
            "Can't determine shape from dimension names: {}".format(" ".join(dims))
        )

    return (h, w)

def rgb(ds,
        bands=['nbart_red', 'nbart_green', 'nbart_blue'],
        index=None,
        index_dim='time',
        robust=True,
        percentile_stretch=None,
        col_wrap=4,
        size=6,
        aspect=None,
        savefig_path=None,
        savefig_kwargs={},
        **kwargs):
    
    """
    Takes an xarray dataset and plots RGB images using three imagery 
    bands (e.g ['nbart_red', 'nbart_green', 'nbart_blue']). The `index` 
    parameter allows easily selecting individual or multiple images for 
    RGB plotting. Images can be saved to file by specifying an output 
    path using `savefig_path`.
    
    This function was designed to work as an easier-to-use wrapper 
    around xarray's `.plot.imshow()` functionality.
    
    Last modified: September 2020
    
    Parameters
    ----------  
    ds : xarray Dataset
        A two-dimensional or multi-dimensional array to plot as an RGB 
        image. If the array has more than two dimensions (e.g. multiple 
        observations along a 'time' dimension), either use `index` to 
        select one (`index=0`) or multiple observations 
        (`index=[0, 1]`), or create a custom faceted plot using e.g. 
        `col="time"`.       
    bands : list of strings, optional
        A list of three strings giving the band names to plot. Defaults 
        to '['nbart_red', 'nbart_green', 'nbart_blue']'.
    index : integer or list of integers, optional
        `index` can be used to select one (`index=0`) or multiple 
        observations (`index=[0, 1]`) from the input dataset for 
        plotting. If multiple images are requested these will be plotted
        as a faceted plot.
    index_dim : string, optional
        The dimension along which observations should be plotted if 
        multiple observations are requested using `index`. Defaults to 
        `time`.
    robust : bool, optional
        Produces an enhanced image where the colormap range is computed 
        with 2nd and 98th percentiles instead of the extreme values. 
        Defaults to True.
    percentile_stretch : tuple of floats
        An tuple of two floats (between 0.00 and 1.00) that can be used 
        to clip the colormap range to manually specified percentiles to 
        get more control over the brightness and contrast of the image. 
        The default is None; '(0.02, 0.98)' is equivelent to 
        `robust=True`. If this parameter is used, `robust` will have no 
        effect.
    col_wrap : integer, optional
        The number of columns allowed in faceted plots. Defaults to 4.
    size : integer, optional
        The height (in inches) of each plot. Defaults to 6.
    aspect : integer, optional
        Aspect ratio of each facet in the plot, so that aspect * size 
        gives width of each facet in inches. Defaults to None, which 
        will calculate the aspect based on the x and y dimensions of 
        the input data.
    savefig_path : string, optional
        Path to export image file for the RGB plot. Defaults to None, 
        which does not export an image file.
    savefig_kwargs : dict, optional
        A dict of keyword arguments to pass to 
        `matplotlib.pyplot.savefig` when exporting an image file. For 
        all available options, see: 
        https://matplotlib.org/api/_as_gen/matplotlib.pyplot.savefig.html        
    **kwargs : optional
        Additional keyword arguments to pass to `xarray.plot.imshow()`.
        For example, the function can be used to plot into an existing
        matplotlib axes object by passing an `ax` keyword argument.
        For more options, see:
        http://xarray.pydata.org/en/stable/generated/xarray.plot.imshow.html  
        
    Returns
    -------
    An RGB plot of one or multiple observations, and optionally an image
    file written to file.
    
    """

    # Get names of x and y dims
    # TODO: remove geobox and try/except once datacube 1.8 is default
    try:
        y_dim, x_dim = ds.geobox.dimensions
    except AttributeError:
        from datacube.utils import spatial_dims
        y_dim, x_dim = spatial_dims(ds)

    # If ax is supplied via kwargs, ignore aspect and size
    if 'ax' in kwargs:
        
        # Create empty aspect size kwarg that will be passed to imshow
        aspect_size_kwarg = {}    
    else:
        # Compute image aspect
        if not aspect:
            #aspect = image_aspect(ds)
            h, w = image_shape(ds)
            asepect = w / h

        
        # Populate aspect size kwarg with aspect and size data
        aspect_size_kwarg = {'aspect': aspect, 'size': size}

    # If no value is supplied for `index` (the default), plot using default 
    # values and arguments passed via `**kwargs`
    if index is None:
        
        # Select bands and convert to DataArray
        da = ds[bands].to_array().compute()

        # If percentile_stretch == True, clip plotting to percentile vmin, vmax
        if percentile_stretch:
            vmin, vmax = da.quantile(percentile_stretch).values
            kwargs.update({'vmin': vmin, 'vmax': vmax})        
        
        # If there are more than three dimensions and the index dimension == 1, 
        # squeeze this dimension out to remove it
        if ((len(ds.dims) > 2) and 
            ('col' not in kwargs) and 
            (len(da[index_dim]) == 1)):
        
            da = da.squeeze(dim=index_dim)
            
        # If there are more than three dimensions and the index dimension
        # is longer than 1, raise exception to tell user to use 'col'/`index`
        elif ((len(ds.dims) > 2) and 
              ('col' not in kwargs) and 
              (len(da[index_dim]) > 1)):
                
            raise Exception(
                f'The input dataset `ds` has more than two dimensions: '
                f'{list(ds.dims.keys())}. Please select a single observation '
                'using e.g. `index=0`, or enable faceted plotting by adding '
                'the arguments e.g. `col="time", col_wrap=4` to the function ' 
                'call'
            )

        img = da.plot.imshow(x=x_dim,
                             y=y_dim,
                             robust=robust,
                             col_wrap=col_wrap,
                             **aspect_size_kwarg,
                             **kwargs)

    # If values provided for `index`, extract corresponding observations and 
    # plot as either single image or facet plot
    else:

        # If a float is supplied instead of an integer index, raise exception
        if isinstance(index, float):
            raise Exception(
                f'Please supply `index` as either an integer or a list of '
                'integers'
            )

        # If col argument is supplied as well as `index`, raise exception
        if 'col' in kwargs:
            raise Exception(
                f'Cannot supply both `index` and `col`; please remove one and '
                'try again'
            )

        # Convert index to generic type list so that number of indices supplied
        # can be computed
        index = index if isinstance(index, list) else [index]

        # Select bands and observations and convert to DataArray
        da = ds[bands].isel(**{index_dim: index}).to_array().compute()

        # If percentile_stretch == True, clip plotting to percentile vmin, vmax
        if percentile_stretch:
            vmin, vmax = da.quantile(percentile_stretch).values
            kwargs.update({'vmin': vmin, 'vmax': vmax})

        # If multiple index values are supplied, plot as a faceted plot
        if len(index) > 1:

            img = da.plot.imshow(x=x_dim,
                                 y=y_dim,
                                 robust=robust,
                                 col=index_dim,
                                 col_wrap=col_wrap,
                                 **aspect_size_kwarg,
                                 **kwargs)

        # If only one index is supplied, squeeze out index_dim and plot as a 
        # single panel
        else:

            img = da.squeeze(dim=index_dim).plot.imshow(robust=robust,
                                                        **aspect_size_kwarg,
                                                        **kwargs)

    # If an export path is provided, save image to file. Individual and 
    # faceted plots have a different API (figure vs fig) so we get around this 
    # using a try statement:
    if savefig_path:

        print(f'Exporting image to {savefig_path}')

        try:
            img.fig.savefig(savefig_path, **savefig_kwargs)
        except:
            img.figure.savefig(savefig_path, **savefig_kwargs)
            
def create_median_mosaic(dataset_in, clean_mask=None, no_data=-9999, dtype=None, **kwargs):
    """
    Method for calculating the median pixel value for a given dataset.
    Parameters
    ----------
    dataset_in: xarray.Dataset
        A dataset retrieved from the Data Cube; should contain:
        coordinates: time, latitude, longitude
        variables: variables to be mosaicked (e.g. red, green, and blue bands)
    clean_mask: np.ndarray
        An ndarray of the same shape as `dataset_in` - specifying which values to mask out.
        If no clean mask is specified, then all values are kept during compositing.
    no_data: int or float
        The no data value.
    dtype: str or numpy.dtype
        A string denoting a Python datatype name (e.g. int, float) or a NumPy dtype (e.g.
        np.int16, np.float32) to convert the data to.
    Returns
    -------
    dataset_out: xarray.Dataset
        Compositited data with the format:
        coordinates: latitude, longitude
        variables: same as dataset_in
    """
    # Default to masking nothing.
    if clean_mask is None:
        clean_mask = create_default_clean_mask(dataset_in)

    # Save dtypes because masking with Dataset.where() converts to float64.
    band_list = list(dataset_in.data_vars)
    dataset_in_dtypes = {}
    for band in band_list:
        dataset_in_dtypes[band] = dataset_in[band].dtype

    # Mask out clouds and Landsat 7 scan lines.
    dataset_in = dataset_in.where(dataset_in > 0 )
    dataset_out = dataset_in.median(dim='time', skipna=True, keep_attrs=False)

    # Handle datatype conversions.
    dataset_out = restore_or_convert_dtypes(dtype, band_list, dataset_in_dtypes, dataset_out, no_data)
    return dataset_out

def create_default_clean_mask(dataset_in):
    """
    Description:
        Creates a data mask that masks nothing.
    -----
    Inputs:
        dataset_in (xarray.Dataset) - dataset retrieved from the Data Cube.
    Throws:
        ValueError - if dataset_in is an empty xarray.Dataset.
    """
    data_vars = dataset_in.data_vars
    if len(data_vars) != 0:
        first_data_var = next(iter(data_vars))
        clean_mask = np.ones(dataset_in[first_data_var].shape).astype(np.bool)
        return clean_mask
    else:
        raise ValueError('`dataset_in` has no data!')

def restore_or_convert_dtypes(dtype_for_all, band_list, dataset_in_dtypes, dataset_out, no_data):
    """
    Restores original datatypes to data variables in Datasets
    output by mosaic functions.
    Parameters
    ----------
    dtype_for_all: str or numpy.dtype
        A string denoting a Python datatype name (e.g. int, float) or a NumPy dtype (e.g.
        np.int16, np.float32) to convert the data to.
    band_list: list-like
        A list-like of the data variables in the dataset.
    dataset_in_dtypes: dict
        A dictionary mapping band names to datatypes.
    no_data: int or float
        The no data value.
    Returns
    -------
    dataset_out: xarray.Dataset
        The output Dataset.
    """
    if dtype_for_all is not None:
        # Integer types can't represent nan.
        if np.issubdtype(dtype_for_all, np.integer): # This also works for Python int type.
            utilities.nan_to_num(dataset_out, no_data)
        convert_to_dtype(dataset_out, dtype_for_all)
    else:  # Restore dtypes to state before masking.
        for band in band_list:
            band_dtype = dataset_in_dtypes[band]
            if np.issubdtype(band_dtype, np.integer):
                nan_to_num(dataset_out[band], no_data)
            dataset_out[band] = dataset_out[band].astype(band_dtype)
    return dataset_out

def nan_to_num(data, number):
    """
    Converts all nan values in `data` to `number`.
    Parameters
    ----------
    data: xarray.Dataset or xarray.DataArray
    """
    if isinstance(data, xr.Dataset):
        for key in list(data.data_vars):
            data[key].values[np.isnan(data[key].values)] = number
    elif isinstance(data, xr.DataArray):
        data.values[np.isnan(data.values)] = number
        
def export_slice_to_geotiff(ds, path):
    """
    Exports a single slice of an xarray.Dataset as a GeoTIFF.
    
    ds: xarray.Dataset
        The Dataset to export.
    path: str
        The path to store the exported GeoTIFF.
    """
    kwargs = dict(tif_path=path, dataset=ds.astype(np.float32), bands=list(ds.data_vars.keys()))
    if 'crs' in ds.attrs:
        kwargs['crs'] = str(ds.attrs['crs'])
    write_geotiff_from_xr(**kwargs)

def export_xarray_to_geotiff(ds, path):
    """
    Exports an xarray.Dataset as individual time slices.
    
    Parameters
    ----------
    ds: xarray.Dataset
        The Dataset to export.
    path: str
        The path prefix to store the exported GeoTIFFs. For example, 'geotiffs/mydata' would result in files named like
        'mydata_2016_12_05_12_31_36.tif' within the 'geotiffs' folder.
    """
    def time_to_string(t):
        return time.strftime("%Y_%m_%d_%H_%M_%S", time.gmtime(t.astype(int)/1000000000))
    
    for t in ds.time:
        time_slice_xarray = ds.sel(time = t)
        export_slice_to_geotiff(time_slice_xarray,
                                path + "_" + time_to_string(t) + ".tif")
        
def write_geotiff_from_xr(tif_path, dataset, bands, no_data=-9999, crs="EPSG:27700"):
    """Write a geotiff from an xarray dataset.
    Args:
        tif_path: path for the tif to be written to.
        dataset: xarray dataset
        bands: list of strings representing the bands in the order they should be written
        no_data: nodata value for the dataset
        crs: requested crs.
    """
    assert isinstance(bands, list), "Bands must a list of strings"
    assert len(bands) > 0 and isinstance(bands[0], str), "You must supply at least one band."
    with rasterio.open(
            tif_path,
            'w',
            driver='GTiff',
            height=dataset.dims['y'],
            width=dataset.dims['x'],
            count=len(bands),
            dtype=dataset[bands[0]].dtype,#str(dataset[bands[0]].dtype),
            crs=crs,
            transform=_get_transform_from_xr(dataset),
            nodata=no_data) as dst:
        for index, band in enumerate(bands):
            dst.write(dataset[band].values, index + 1)
        dst.close()
        
def _get_transform_from_xr(dataset):
    """Create a geotransform from an xarray dataset.
    """

    from rasterio.transform import from_bounds
    geotransform = from_bounds(dataset.x[0], dataset.y[-1], dataset.x[-1], dataset.y[0],
                               len(dataset.x), len(dataset.y))
    return geotransform

def change_detection(ds, time_baseline='2020-05-01'):

    # Make samples
    baseline_sample = ds.sel(time=ds['time']<=np.datetime64(time_baseline))
    print(f"Number of observations in baseline sample: {len(baseline_sample.time)}")

    postbaseline_sample = ds.sel(time=ds['time']>np.datetime64(time_baseline))
    print(f"Number of observations in postbaseline sample: {len(postbaseline_sample.time)}")

    # Record coodrinates for reconstructing xarray objects
    sample_lat_coords = ds.coords['y']
    sample_lon_coords = ds.coords['x']
    
    # Perform the t-test on the postbaseline and baseline samples
    tstat, p_tstat = stats.ttest_ind(
        postbaseline_sample.values,
        baseline_sample.values,
        equal_var=False,
        nan_policy='omit',
    )

    # Convert results to an xarray for further analysis
    t_test = xr.Dataset(
        {
            't_stat': (['y', 'x'], tstat),
            'p_val': (['y', 'x'], p_tstat)
        },
        coords={
            'x': (['x'], sample_lon_coords.values),
            'y': (['y'], sample_lat_coords.values)
        }, 
        attrs={
            'crs': 'EPSG:3577',
        })

    # Set the significance level
    sig_level = 0.05

    # Plot any difference in the mean
    diff_mean = postbaseline_sample.mean(dim=['time']) - baseline_sample.mean(dim=['time'])

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    diff_mean.plot(cmap='RdBu')
    ax.set_title('Any difference in the mean')
    plt.show()

    # Plot any difference in the mean classified as significant
    sig_diff_mean = postbaseline_sample.mean(dim=['time']).where(t_test.p_val < sig_level) - baseline_sample.mean(dim=['time']).where(t_test.p_val < sig_level)

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    sig_diff_mean.plot(cmap='RdBu')
    ax.set_title('Statistically significant difference in the mean')
    plt.show()
    
def xr_rasterize(gdf,
                 da,
                 attribute_col=False,
                 crs=None,
                 transform=None,
                 name=None,
                 x_dim='x',
                 y_dim='y',
                 export_tiff= None,
                 **rasterio_kwargs):    
    """
    Rasterizes a geopandas.GeoDataFrame into an xarray.DataArray.
    
    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        A geopandas.GeoDataFrame object containing the vector/shapefile
        data you want to rasterise.
    da : xarray.DataArray
        The shape, coordinates, dimensions, and transform of this object 
        are used to build the rasterized shapefile. It effectively 
        provides a template. The attributes of this object are also 
        appended to the output xarray.DataArray.
    attribute_col : string, optional
        Name of the attribute column in the geodataframe that the pixels 
        in the raster will contain.  If set to False, output will be a 
        boolean array of 1's and 0's.
    crs : str, optional
        CRS metadata to add to the output xarray. e.g. 'epsg:3577'.
        The function will attempt get this info from the input 
        GeoDataFrame first.
    transform : affine.Affine object, optional
        An affine.Affine object (e.g. `from affine import Affine; 
        Affine(30.0, 0.0, 548040.0, 0.0, -30.0, "6886890.0) giving the 
        affine transformation used to convert raster coordinates 
        (e.g. [0, 0]) to geographic coordinates. If none is provided, 
        the function will attempt to obtain an affine transformation 
        from the xarray object (e.g. either at `da.transform` or
        `da.geobox.transform`).
    x_dim : str, optional
        An optional string allowing you to override the xarray dimension 
        used for x coordinates. Defaults to 'x'.    
    y_dim : str, optional
        An optional string allowing you to override the xarray dimension 
        used for y coordinates. Defaults to 'y'.
    export_tiff: str, optional
        If a filepath is provided (e.g 'output/output.tif'), will export a
        geotiff file. A named array is required for this operation, if one
        is not supplied by the user a default name, 'data', is used
    **rasterio_kwargs : 
        A set of keyword arguments to rasterio.features.rasterize
        Can include: 'all_touched', 'merge_alg', 'dtype'.
    
    Returns
    -------
    xarr : xarray.DataArray
    
    """
    
    # Check for a crs object
    try:
        crs = da.crs
    except:
        if crs is None:
            raise Exception("Please add a `crs` attribute to the "
                            "xarray.DataArray, or provide a CRS using the "
                            "function's `crs` parameter (e.g. 'EPSG:3577')")
    

    # Check if transform is provided as a xarray.DataArray method.
    # If not, require supplied Affine
    if transform is None:
        try:
            # First, try to take transform info from geobox
            transform = da.geobox.transform
        # If no geobox
        except:
            try:
                # Try getting transform from 'transform' attribute
                transform = da.transform
            except:
                # If neither of those options work, raise an exception telling the 
                # user to provide a transform
                raise Exception("Please provide an Affine transform object using the "
                        "`transform` parameter (e.g. `from affine import "
                        "Affine; Affine(30.0, 0.0, 548040.0, 0.0, -30.0, "
                        "6886890.0)`")
    
    # Get the dims, coords, and output shape from da
    da = da.squeeze()
    y, x = da.shape
    dims = list(da.dims)
    xy_coords = [da[y_dim], da[x_dim]]   
    
    # Reproject shapefile to match CRS of raster
    print(f'Rasterizing to match xarray.DataArray dimensions ({y}, {x}) '
          f'and projection system/CRS (e.g. {crs})')
    
    try:
        gdf_reproj = gdf.to_crs(crs=crs)
    except:
        #sometimes the crs can be a datacube utils CRS object
        #so convert to string before reprojecting
        gdf_reproj = gdf.to_crs(crs={'init':str(crs)})
    
    # If an attribute column is specified, rasterise using vector 
    # attribute values. Otherwise, rasterise into a boolean array
    if attribute_col:
        
        # Use the geometry and attributes from `gdf` to create an iterable
        shapes = zip(gdf_reproj.geometry, gdf_reproj[attribute_col])

        # Convert polygons into a numpy array using attribute values
        arr = rasterio.features.rasterize(shapes=shapes,
                                          out_shape=(y, x),
                                          transform=transform,
                                          **rasterio_kwargs)
    else:
        # Convert polygons into a boolean numpy array 
        arr = rasterio.features.rasterize(shapes=gdf_reproj.geometry,
                                          out_shape=(y, x),
                                          transform=transform,
                                          **rasterio_kwargs)
        
    # Convert result to a xarray.DataArray
    if name is not None:
        xarr = xr.DataArray(arr,
                           coords=xy_coords,
                           dims=dims,
                           attrs=da.attrs,
                           name=name)
    else:
        xarr = xr.DataArray(arr,
                   coords=xy_coords,
                   dims=dims,
                   attrs=da.attrs)
    
    #add back crs if da.attrs doesn't have it
    if 'crs' not in xarr.attrs:
        xarr.attrs['crs'] = str(crs)
    
    if export_tiff:
            try:
                print("Exporting GeoTIFF with array name: " + name)
                ds = xarr.to_dataset(name = name)
                #xarray bug removes metadata, add it back
                ds[name].attrs = xarr.attrs 
                ds.attrs = xarr.attrs
                write_geotiff(export_tiff, ds) 
                
            except:
                print("Exporting GeoTIFF with default array name: 'data'")
                ds = xarr.to_dataset(name = 'data')
                ds.data.attrs = xarr.attrs
                ds.attrs = xarr.attrs
                write_geotiff(export_tiff, ds)
                
    return xarr