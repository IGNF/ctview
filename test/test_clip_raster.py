import os
import shutil

from osgeo import gdal

from ctview.utils_pdal import get_bounds_from_las

gdal.UseExceptions()

DIR_LAS = os.path.join("data", "las")
DIR_RASTER = os.path.join("data", "raster")
IN_LAS = os.path.join(DIR_LAS, "test_data_0000_0000_LA93_IGN69_ground.las")
IN_RASTER = os.path.join(DIR_RASTER, "test_data_0000_0000_LA93_IGN69_ground.tif")
OUTPUT_DIR = os.path.join("tmp", "clip_raster")
OUT_RASTER = os.path.join(OUTPUT_DIR, "test_data_0000_0000_LA93_IGN69_ground_crop.tif")


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)

    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR)


([xmin_las, xmax_las], [ymin_las, ymax_las]) = get_bounds_from_las(in_las=IN_LAS)

maxx_Modif = xmax_las - 5
minx_Modif = xmin_las + 5
maxy_Modif = ymax_las - 5
miny_Modif = ymin_las + 5

maxx_Expected = 770545
minx_Expected = 770505
maxy_Expected = 6277545
miny_Expected = 6277505
