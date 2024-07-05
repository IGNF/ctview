import os

from osgeo_utils import gdal_fillnodata

from ctview import utils_gdal


def fill_gaps_raster(in_raster: str, output_file: str, raster_driver: str):
    """Fill gaps on a raster using gdal.

    Args:
        in_raster (str): path to the raster to fill
        output_file (str): full path to the output raster
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)

    Raises:
        FileNotFoundError: if the output raster has not been created
    """

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    gdal_fillnodata.gdal_fillnodata(
        src_filename=in_raster,
        band_number=2,
        dst_filename=output_file,
        driver_name=raster_driver,
        creation_options=None,
        quiet=True,
        mask="default",
        max_distance=2,
        smoothing_iterations=0,
        options=None,
    )

    if not os.path.exists(output_file):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{output_file} not found")


def add_color_to_raster(in_raster: str, output_file: str, LUT: str):
    """Color a raster using method gdal DEMProcessing with a specific LUT.

    Args:
        in_raster (str): path to the input raster (to be colored)
        output_file (str): full path to the output raster
        LUT (str): path to the LUT used to color the raster

    Raises:
        FileNotFoundError: if the output raster has not been created
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    utils_gdal.color_raster_with_LUT(input_raster=in_raster, output_raster=output_file, LUT=LUT)

    if not os.path.exists(output_file):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{output_file} not found")
