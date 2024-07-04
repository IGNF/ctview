import os
from typing import List, Tuple

from osgeo import gdal


def clip_raster(input_raster: str, output_raster: str, bounds: Tuple | List, raster_driver: str):
    """Clip raster to the expected shape

    Args:
        input_raster (str): path to the input raster
        output_raster (str): path to the output raster
        bounds (Tuple | List): boundaries to clip to, as ((minx, maxx), (miny, maxy))
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)
    """
    os.makedirs(os.path.dirname(output_raster), exist_ok=True)
    minX, minY, maxX, maxY = bounds[0][0], bounds[1][0], bounds[0][1], bounds[1][1]
    gdal.Warp(output_raster, input_raster, format=raster_driver, outputBounds=[minX, minY, maxX, maxY])
