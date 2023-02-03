# Autor : ELucon

# IMPORT

# File
import ctview.utils_pdal as utils_pdal
import ctview.utils_gdal as utils_gdal
import ctview.utils_tools as utils_tools
    # Library
import os
import pdal
import numpy
import argparse
import subprocess
import logging as log
    # Dictionnary
from ctview.parameter import dico_param
from ctview.utils_folder import dico_folder
import lidarutils.gdal_calc as gdal_calc

# PARAMETERS

EPSG = dico_param["EPSG"]
resolution = dico_param["resolution_DTM_dens"]
extension = dico_param["raster_extension"]
FOLDER_DENS_VALUE = dico_folder["folder_density_value"]
FOLDER_DENS_COLOR = dico_folder["folder_density_color"]
FOLDER_DENS_FINAL = dico_folder["folder_density_final"]

# FONCTION


def generate_raster_of_density(
    input_las: str,
    output_dir: str
):
    """
    Build a raster of density colored.
    Args :
        input_las : las file
        output_dir : output directory
    Return :
        path of the raster of density colored
    """
    # Get directory
    input_dir = os.path.dirname(input_las)
    # Get filename without extension
    input_filename = os.path.basename(input_las)

    # Build raster count point
    raster_name_count = os.path.join(output_dir,FOLDER_DENS_VALUE,f"{os.path.splitext(input_filename)[0]}_COUNT{extension}")
    raster_name_dens = os.path.join(output_dir, FOLDER_DENS_VALUE,f"{os.path.splitext(input_filename)[0]}_DENS{extension}")

    # Parameters
    size = resolution  # meter = resolution from raster
    _size = utils_tools.give_name_resolution_raster(size)

    # Get bounds
    bounds_las = utils_pdal.get_bounds_from_las(input_las) # get boundaries
    log.info(f"Bounds : {bounds_las}")
    # Remove 1 pixel from bounds
    bounds_las_crop = utils_tools.remove_1_pixel(bounds=bounds_las, resolution=dico_param["resolution_DTM_dens"])
    
    # Raster of density : count points in resolution*resolution m² (Default=25 m²)
    log.info(f"Raster count points at resolution {size} meter(s)")
    method_writer_gdal(input_las=input_las, output_file=raster_name_count, bounds=bounds_las_crop)

    # Crop raster


    # Overwrite and change unity of count from "per 25 m²" to "per m²"
    change_unit(
        input_raster=raster_name_count,
        output_raster=raster_name_dens,
        res=resolution
        )

    # Color density
    raster_name_dens_color = os.path.join(output_dir, FOLDER_DENS_COLOR,f"{os.path.splitext(input_filename)[0]}_DENS_COLOR{extension}")

    log.info("Colorisation...")
    utils_gdal.color_raster_with_LUT(
        input_raster = raster_name_dens,
        output_raster = raster_name_dens_color,
        LUT = os.path.join("..","LUT","LUT_DENSITY.txt")
    )

    return raster_name_dens_color


def method_writer_gdal(
    input_las: str,
    output_file: str,
    bounds: str = None
):
    log.info(f"Bounds forced (remove 1 pixel at resolution density) :{bounds}")
    if bounds is None :
        pipeline = (
            pdal.Reader.las(filename=input_las)
            | pdal.Filter.range(
                            limits="Classification[2:2]"
                            )
            | pdal.Writer.gdal(
                            filename = output_file, 
                            resolution = resolution,
                            radius = resolution,
                            output_type = "count"
                            )
        )
    else :
        pipeline = (
            pdal.Reader.las(filename=input_las)
            | pdal.Filter.range(
                            limits="Classification[2:2]"
                            )
            | pdal.Writer.gdal(
                            filename = output_file, 
                            resolution = resolution,
                            radius = 0.1,
                            output_type = "count",
                            bounds = str(bounds),
                            )
        )
    pipeline.execute()


def change_unit(input_raster: str, output_raster: str, res: int):
    """
    Overwrite and change unity of count from "per res*res m²" to "per m²
    Args :
        raster_name : raster of density with units res*res m²
        res : resolution of the raster
    """
    gdal_calc.Calc(
        f"A/{res*res}",
        outfile=output_raster,
        A=input_raster,
        quiet=True,
    )


def multiply_DTM_density(input_DTM: str, input_dens_raster: str, filename: str, output_dir: str):

    # Output file
    out_raster = os.path.join(output_dir, FOLDER_DENS_FINAL, f"{os.path.splitext(filename)[0]}_DENS{extension}")
    # Mutiply 
    gdal_calc.Calc(
        A=input_DTM,
        B=input_dens_raster,
        calc="((A-1)<0)*B*(A/255)+((A-1)>=0)*B*((A-1)/255)",
        outfile=out_raster
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-idir", "--input_las")
    parser.add_argument('-odir', '--output_dir')

    return parser.parse_args()

if __name__=="__main__":

    args = parse_args()
    input_las = args.input_las
    output_dir = args.output_dir

    # Create directory if not exists
    if os.path.exists(out_dir):
        # Clean folder test if exists
        shutil.rmtree(out_dir)
    else:
        # Create folder test if not exists
        os.makedirs(out_dir)
    os.makedirs(os.path.join(output_dir,FOLDER_DENS_VALUE), exist_ok=True)
    os.makedirs(os.path.join(output_dir,FOLDER_DENS_COLOR), exist_ok=True)

    generate_raster_of_density(input_las = input_las, output_dir=output_dir)
