import fnmatch
import re
import os
import tempfile

from osgeo import gdal, osr


def add_epsg_to_raster(raster: str, epsg: int):
    """add epsg to raster"""
    gdal_image = gdal.Open(raster)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    gdal_image.SetProjection(srs.ExportToWkt())


def get_raster_corner_coord(in_raster: str):
    """
    Get corners coordinates from a raster
    Return :
        tuple(upper_left_x,upper_left_y,lower_right_x,lower_right_y)
        """
    gtif = gdal.Open(in_raster)
    ulx, xres, xskew, uly, yskew, yres  = gtif.GetGeoTransform()
    lrx = ulx + (gtif.RasterXSize * xres)
    lry = uly + (gtif.RasterYSize * yres)
    return (ulx,uly,lrx,lry)


def transform_CornerCoord_to_Bounds(corner_coord: tuple):
    """
    Transform corners coordinates to maximum and minimum x and y
    Warning : 
        corner_coord must be in this order : (upper_left_x,upper_left_y,lower_right_x,lower_right_y)
    Return :
        ([minx,maxx],[miny,maxy])
    """
    _X = [corner_coord[0],corner_coord[2]]
    _Y = [corner_coord[1],corner_coord[3]]

    _X.sort() # arrange in ascending order
    _Y.sort()

    return (_X,_Y)


def color_raster_with_LUT(input_raster, output_raster, LUT):
    """
    Color raster with a LUT
    input_raster : path of raster to colorise
    output_raster : path of raster colorised
    dim : dimension to color
    LUT : dictionnary of color
    """

    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing="color-relief",
        colorFilename=LUT,
    )
