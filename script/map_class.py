# Autor : ELucon

# IMPORT

# Library
import pdal
import tools
import sys
import logging as log
import os
import argparse

from osgeo import gdal
from typing import Optional
from numbers import Real


# Library intern
import utils_gdal
from osgeo_utils import gdal_fillnodata


# FONCTION


def fill_gaps(input_raster):
    """
    NO FONKTIONIERT
    Fill selected raster regions by interpolation from the edges.
    This algorithm will interpolate values for all designated nodata pixels.
    The default mask band used is the one returned by GDALGetMaskBand(hTargetBand).
    """
    opened_raster = gdal.OpenEx(input_raster)
    band_raster = gdal.Dataset.GetRasterBand(opened_raster, 1)
    mask_band_raster = gdal.Band.GetMaskBand(band_raster)

    gdal.FillNodata(
        targetBand=band_raster,
        maskBand=mask_band_raster,
        maxSearchDist=2,
        smoothingIterations=0,
    )


def fill_no_data(
    src_raster: Optional[str] = None,
    dst_raster: Optional[str] = None,
    max_Search_Distance: Real = 2,
):
    """Fill gap in the data.
    input_raster : raster to fill
    output_raster : raster with no gap
    max_Search_Distance : maximum distance (in pixel) that the algorithm will search out for values to interpolate.
    """
    gdal_fillnodata.gdal_fillnodata(
        src_filename=src_raster,
        band_number=2,
        dst_filename=dst_raster,
        driver_name="GTiff",
        creation_options=None,
        quiet=True,
        mask="default",
        max_distance=max_Search_Distance,
        smoothing_iterations=0,
        options=None,
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-las", "--input_las")
    parser.add_argument("-o", "--output_dir")

    return parser.parse_args()


def main():

    log.basicConfig(level=log.INFO)

    # Get las file, output directory and interpolation method
    args = parse_args()
    input_las = args.input_las
    output_dir = args.output_dir

    # Clean folder
    for filename in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, filename))

    input_las_name = os.path.basename(input_las)
    input_las_name_without_extension = os.path.splitext(input_las_name)[0]  # Read las
    in_points = tools.read_las(input_las)

    log.info(f"\n\nMAP OF CLASS : file : {input_las_name}")

    # Write raster
    output_raster = os.path.join(
        output_dir, f"{input_las_name_without_extension}_raster.tif"
    )
    tools.write_raster_class(in_points, output_raster)

    log.info("Create raster of class brut : ")
    log.info(output_raster)

    if not os.path.exists(output_raster):
        print(f"FileNotFoundError : {output_raster} not found")
        sys.exit()

    # Fill gaps
    fillgap_raster = os.path.join(
        output_dir, f"{input_las_name_without_extension}_raster_fillgap.tif"
    )

    fill_no_data(
        src_raster=output_raster,
        dst_raster=fillgap_raster,
        max_Search_Distance=2,  # modif 10/01/2023
    )

    log.info("Fill gaps : ")
    log.info(fillgap_raster)

    if not os.path.exists(fillgap_raster):
        print(f"FileNotFoundError : {fillgap_raster} not found")
        sys.exit()

    # Color fill gaps
    color_fillgap_raster = os.path.join(
        output_dir, f"{input_las_name_without_extension}_raster_fillgap_color.tif"
    )
    tools.color_raster_by_class_2(
        input_raster=fillgap_raster,
        output_raster=color_fillgap_raster,
    )

    log.info("Color fill gaps raster : ")
    log.info(color_fillgap_raster)

    if not os.path.exists(color_fillgap_raster):
        print(f"FileNotFoundError : {color_fillgap_raster} not found")
        sys.exit()

    # Color fill
    color_raster = os.path.join(
        output_dir, f"{input_las_name_without_extension}_raster_color_.tif"
    )
    tools.color_raster_by_class_2(
        input_raster=output_raster,
        output_raster=color_raster,
    )

    log.info("Color raster brut: ")
    log.info(color_raster)

    if not os.path.exists(color_raster):
        print(f"FileNotFoundError : {color_raster} not found")
        sys.exit()


if __name__ == "__main__":

    main()
