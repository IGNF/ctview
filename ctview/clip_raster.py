from typing import List, Tuple

from osgeo import gdal

gdal.UseExceptions()


def crop_raster(input_raster: str, output_raster: str, bounds: str):
    """
    Crop a raster with bounds extract from las at the origin of the raster.
    Args :
        input_raster : raster to crop
        output_raster : filename of raster that will be croped
        bounds : ([minx,maxx],[miny, maxy])
    """
    ulx = bounds[0][0]  # upper-left x = minx
    uly = bounds[1][1]  # upper-left y = maxy
    lrx = bounds[0][1]  # lower-right x = maxx
    lry = bounds[1][0]  # lower-right y = miny

    window = (ulx, uly, lrx, lry)

    gdal.Translate(srcDS=input_raster, destName=output_raster, projWin=window)


def clip_raster(input_raster: str, output_raster: str, bounds: Tuple | List, raster_driver: str):
    """Clip raster to the expected shape

    Args:
        input_raster (str): path to the input raster
        output_raster (str): path to the output raster
        bounds (Tuple | List): boundaries to clip to, as ((minx, maxx), (miny, maxy))
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)
    """
    minX, minY, maxX, maxY = bounds[0][0], bounds[1][0], bounds[0][1], bounds[1][1]
    gdal.Warp(output_raster, input_raster, format=raster_driver, outputBounds=[minX, minY, maxX, maxY])
