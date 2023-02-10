# Autor : ELucon

# IMPORT

# Library
import pdal
import ctview.utils_tools as utils_tools
import ctview.utils_pdal as utils_pdal
import logging as log
import os
import argparse

from osgeo import gdal
from typing import Optional
from numbers import Real


# Library intern
import ctview.utils_gdal as utils_gdal
from osgeo_utils import gdal_fillnodata

# Dictionnary
from ctview.utils_folder import dico_folder
from ctview.parameter import dico_param

# Parameters
resolution_class = dico_param["resolution_mapclass"]


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


def main(input_las: str(), output_dir: str()):

    log.basicConfig(level=log.INFO, format='%(message)s')

    # File names
    input_las_name = os.path.basename(input_las)
    input_las_name_without_extension = os.path.splitext(input_las_name)[0]  # Read las
    in_points = utils_pdal.read_las(input_las)

    log.info(f"\nMAP OF CLASS : file : {input_las_name}")

    # Output_folder_names
    output_folder_1 = os.path.join(output_dir,dico_folder["folder_CC_brut"])
    output_folder_2 = os.path.join(output_dir,dico_folder["folder_CC_fillgap"])
    output_folder_3 = os.path.join(output_dir,dico_folder["folder_CC_brut_color"])
    output_folder_4 = os.path.join(output_dir,dico_folder["folder_CC_fillgap_color"])
    output_folder_5 = os.path.join(output_dir,dico_folder["folder_CC_fusion"])

    # Step 1 : Write raster brut
    raster_brut = os.path.join(
        output_folder_1, f"{input_las_name_without_extension}_raster.tif"
    )
    log.info(f"Step 1/5 : Raster of class brut : {raster_brut}")
    utils_pdal.write_raster_class(input_points=in_points, output_raster=raster_brut, res=resolution_class)

    if not os.path.exists(raster_brut): # if raster_brut not create, next step with fail
        raise FileNotFoundError (f"{raster_brut} not found")

    # Step 2 :  Fill gaps
    fillgap_raster = os.path.join(
        output_folder_2, f"{input_las_name_without_extension}_raster_fillgap.tif"
    )
    log.info(f"Step 2/5 : Fill gaps : {fillgap_raster}")

    fill_no_data(
        src_raster=raster_brut,
        dst_raster=fillgap_raster,
        max_Search_Distance=2,  # modif 10/01/2023
    )

    if not os.path.exists(fillgap_raster): # if raster_brut not create, next step with fail
        raise FileNotFoundError (f"{fillgap_raster} not found")

    # Color fill gaps
    color_fillgap_raster = os.path.join(
        output_dir, f"{input_las_name_without_extension}_raster_fillgap_color.tif"
    )
    utils_gdal.color_raster_by_class_2(
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
    utils_gdal.color_raster_by_class_2(
        input_raster=raster_brut,
        output_raster=color_raster,
    )

    log.info("Color raster brut: ")
    log.info(color_raster)

    if not os.path.exists(color_raster):
        print(f"FileNotFoundError : {color_raster} not found")
        sys.exit()


if __name__ == "__main__":

    # Get las file, output directory and interpolation method
    args = parse_args()
    in_las = args.input_las
    out_dir = args.output_dir

    # Create folders
    os.makedirs(os.path.join(out_dir,dico_folder["folder_CC_brut"]), exist_ok=True)
    os.makedirs(os.path.join(out_dir,dico_folder["folder_CC_fillgap"]), exist_ok=True)
    os.makedirs(os.path.join(out_dir,dico_folder["folder_CC_brut_color"]), exist_ok=True)
    os.makedirs(os.path.join(out_dir,dico_folder["folder_CC_fillgap_color"]), exist_ok=True)
    os.makedirs(os.path.join(out_dir,dico_folder["folder_CC_fusion"]), exist_ok=True)

    main(in_las, out_dir)
