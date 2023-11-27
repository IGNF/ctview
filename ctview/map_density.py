# Autor : ELucon

# IMPORT

# File
import ctview.utils_pdal as utils_pdal
import ctview.utils_gdal as utils_gdal
import ctview.utils_tools as utils_tools
import ctview.clip_raster as clip_raster
    # Library
import os
import pdal
import numpy
import shutil
import argparse
import subprocess
import logging as log
    # Dictionnary
from ctview.parameter import dico_param
from ctview.utils_folder import dico_folder_template
import lidarutils.gdal_calc as gdal_calc

# PARAMETERS

EPSG = dico_param["EPSG"]
resolution = dico_param["resolution_DTM_dens"]
extension = dico_param["raster_extension"]
FOLDER_DENS_VALUE = dico_folder_template["folder_density_value"]
FOLDER_DENS_COLOR = dico_folder_template["folder_density_color"]
_radius = dico_param["radius_PC_dens"]
CLASSIF_GROUND = 2

# FONCTION


def generate_raster_of_density(
    input_las: str,
    output_dir: str,
    bounds: str=None
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

    log.info(f"\nRaster of density at resolution {size} meter(s) : {input_filename}\n")
    
    # Raster of density : count points in resolution*resolution m² (Default=25 m²)
    log.info(f"Raster count points at resolution {size} meter(s)")
    success = method_writer_gdal(input_las=input_las, output_file=raster_name_count, bounds=bounds)

    if success :
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
            LUT = os.path.join("LUT","LUT_DENSITY.txt")
        )

        return raster_name_dens_color, success

    else :
        return "_", success


def method_writer_gdal(
    input_las: str,
    output_file: str,
    bounds: str = None,
    radius=_radius
):
    log.debug('method_writer_gdal')
    log.debug(f"raster name output count points : {output_file}")
    log.debug(f'bounds is : {bounds}')
    log.debug(f"resolution utilisée : {resolution}")
    log.debug(f"radius :{radius}")

    # Check if the las file contains ground points (redmine 2068)
    pts_to_check = utils_pdal.read_las_file(input_las=input_las)
    pts_ground = numpy.where(pts_to_check["Classification"] == CLASSIF_GROUND, 1, 0)
    nb_pts_ground = numpy.count_nonzero(pts_ground == 1)

    is_count_ok = True

    if nb_pts_ground > 0 :

        pipeline = pdal.Filter.range(
                                limits="Classification[2:2]"
                                ).pipeline(pts_to_check)
        

        if bounds is None :
            pipeline |= pdal.Writer.gdal(
                                filename = output_file, 
                                resolution = resolution,
                                radius = radius,
                                output_type = "count"
                                )
        else :
            log.info(f"Bounds forced (remove 1 pixel at resolution density) :{bounds}")
            pipeline |= pdal.Writer.gdal(
                                filename = output_file, 
                                resolution = resolution,
                                radius = radius,
                                output_type = "count",
                                bounds = str(bounds),
                                )

        pipeline.execute()

        return is_count_ok

    else :
        is_count_ok = False
        return is_count_ok


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


def multiply_DTM_density(input_DTM: str, input_dens_raster: str, filename: str, output_dir: str, bounds: tuple, dico_fld: dict):
    """
    Fusion of 2 rasters (DTM and raster of density) with a given formula.
    Args :
        input_DTM : DTM
        input_dens_raster : raster of density
        filename : name of las file whithout path
        output_dir : output directory
        bounds : bounds of las file ([minx,maxx],[miny, maxy])
    """
    # Crop rasters
    log.info("Crop rasters")
    input_DTM_crop = f"{os.path.splitext(input_DTM)[0]}_crop{extension}"
    clip_raster.clip_raster(input_raster=input_DTM, output_raster=input_DTM_crop, bounds=bounds)

    input_dens_raster_crop = f"{os.path.splitext(input_dens_raster)[0]}_crop{extension}"
    clip_raster.clip_raster(input_raster=input_dens_raster, output_raster=input_dens_raster_crop, bounds=bounds)

    log.info("Multiplication with DTM")
    # Output file
    out_raster = os.path.join(output_dir, dico_fld["folder_density_final"], f"{os.path.splitext(filename)[0]}_DENS{extension}")
    # Mutiply 
    gdal_calc.Calc(
        A=input_DTM_crop,
        B=input_dens_raster_crop,
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
    if os.path.exists(output_dir):
        # Clean folder test if exists
        shutil.rmtree(output_dir)
    else:
        # Create folder test if not exists
        os.makedirs(output_dir)
    os.makedirs(os.path.join(output_dir,FOLDER_DENS_VALUE), exist_ok=True)
    os.makedirs(os.path.join(output_dir,FOLDER_DENS_COLOR), exist_ok=True)

    generate_raster_of_density(input_las = input_las, output_dir=output_dir)
