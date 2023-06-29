# Autor : ELucon

# IMPORT

# File
import ctview.utils_tools as utils_tools
import ctview.utils_pdal as utils_pdal
import ctview.utils_gdal as utils_gdal
from ctview.parameter import dico_param
from ctview.utils_folder import dico_folder_template
import ctview.gen_LUT_X_cycle as gen_LUT_X_cycle

# Library
import sys
import pdal
from osgeo import gdal
import numpy as np
import subprocess
import startinpy
import os
from sys import argv
from multiprocessing import Pool, cpu_count
import json
import laspy
import math
from tqdm import tqdm
import logging as log
from typing import List
    # mnx
import produit_derive_lidar as mnx
import pdaltools.las_add_buffer
import produit_derive_lidar.filter_one_tile
import produit_derive_lidar.ip_one_tile

# TEMPORARY
# dico_folder_template = dico_folder_template.copy()

# OUTPUT TREE

def create_output_tree(output_dir: str):
    """Create tree for output. 
    """
    output_tree = {
                "DTM":
                    {"output": os.path.join(output_dir, "DTM"),
                    "filter": os.path.join(output_dir, "tmp_dtm", "filter"),
                    "buffer": os.path.join(output_dir, "tmp_dtm", "buffer"),
                    "hillshade": os.path.join(output_dir, "tmp_dtm", "hillshade"),
                    "color": os.path.join(output_dir, "DTM", "color")
                    },
                "DSM":
                    {"output": os.path.join(output_dir, "DSM"),
                    "filter": os.path.join(output_dir, "tmp_dsm", "filter"),
                    "buffer": os.path.join(output_dir, "tmp_dsm", "buffer"),
                    "hillshade": os.path.join(output_dir, "tmp_dsm", "hillshade")
                    },
                "DTM_DENS":
                    {"output": os.path.join(output_dir, "DTM_DENS"),
                    "filter": os.path.join(output_dir, "tmp_dtm_dens", "filter"),
                    "buffer": os.path.join(output_dir, "tmp_dtm_dens", "buffer"),
                    "hillshade": os.path.join(output_dir, "tmp_dtm_dens", "hillshade"),
                    }
            }

    for n in output_tree :
        os.makedirs(output_tree[n]["output"], exist_ok=True)
        os.makedirs(output_tree[n]["filter"], exist_ok=True)
        os.makedirs(output_tree[n]["buffer"], exist_ok=True)
        os.makedirs(output_tree[n]["hillshade"], exist_ok=True)
    os.makedirs(output_tree["DTM"]["color"], exist_ok=True)

    return output_tree


def run_mnx_filter_las_classes(
                        input_file: str,
                        output_file: str,
                        spatial_reference: str='EPSG:2154',
                        keep_classes: List=[2, 66]):
    """ Reads the LAS file and filter only grounds from LIDAR.

    Args:
        input_file (str) : Path to the input lidar file
        output_file (str): Path to the output file
        spatial_ref (str) : spatial reference to use when reading the las file
        keep_classes (List): Classes to keep in the filter (ground + virtual points by default)
    """
    # run filter
    mnx.tasks.las_filter.filter_las_classes(
                        input_file=input_file,
                        output_file=output_file,
                        spatial_ref=spatial_reference,
                        keep_classes=keep_classes)


def run_pdaltools_buffer(input_dir: str, tile_filename: str,
                           output_filename: str,
                           buffer_width: int=100,
                           tile_width: int=1000,
                           tile_coord_scale: int=1000):
    """Merge lidar tiles around the queried tile and crop them in order to add a buffer
    to the tile (usually 100m).
    Args:
        input_dir (str): directory of pointclouds (where you look for neigbors)
        tile_filename (str): full path to the queried LIDAR tile
        output_filename (str) : full path to the saved cropped tile
        buffer_width (int): width of the border to add to the tile (in pixels)
        spatial_ref (str): Spatial reference to use to override the one from input las.
        tile width (int): width of tiles in meters (usually 1000m)
        tile_coord_scale (int) : scale used in the filename to describe coordinates in meters
                (usually 1000m)
    """
    # param
    spatial_ref_num = dico_param["EPSG"]
    # run buffer
    pdaltools.las_add_buffer.create_las_with_buffer(
                            input_dir, tile_filename, output_filename,
                            buffer_width=buffer_width,
                            spatial_ref=f"EPSG:{spatial_ref_num}",
                            tile_width=tile_width,
                            tile_coord_scale=tile_coord_scale)  


def run_mnx_interpolation(input_file: str, output_raster: str, config: dict):
    """Run interpolation
    Args:
        input_file(str): File on which to run the interpolation
        output_raster(str): output file for raster image (with buffer)
        config(dict): dictionary that must contain
                { "tile_geometry": { "tile_coord_scale": #int, "tile_width": #int, "pixel_size": #float, "no_data_value": #int },
                  "io": { "spatial_reference": #str},
                  "interpolation": { "algo_name": #str }
                }
            with
                tile_coord_scale value(int): coords in tile names are in km
                tile_width value(int): tile width in meters
                pixel_size value(float): pixel size for raster generation
                spatial_ref value(str): spatial reference to use when reading las file
                interpolation_method value(str): interpolation method for raster generation
    """
    mnx.ip_one_tile.interpolate(input_file=input_file,
                output_raster=output_raster,
                config=config)


def add_hillshade_one_raster(input_raster: str, output_raster: str):
    """Add hillshade to raster
    Arg :
        input_raster : input file with complete path
        output_raster : output file with complete path
    """
    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing="hillshade",
    )


def create_mnx_one_las(input_file: str,
            output_dir: str,
            config_dict: dict,
            type_raster="dtm"):
    """
    Create a DTM or a DSM from a las tile.
    Args :
        input_file : full path of LAS/LAZ file
        config_dict :  dictionary that must contain
                { "tile_geometry": { "tile_coord_scale": #int, "tile_width": #int, "pixel_size": #float, "no_data_value": #int },
                  "io": { "spatial_reference": #str},
                  "interpolation": { "algo_name": #str }
                }
        type_raster : can be dtm / dsm / dtm_dens 
    """

    # manage paths
    input_dir, input_basename = os.path.split(input_file)
    tilename, _ = os.path.splitext(input_basename)
    
    # prepare outputs
    output_tree = create_output_tree(output_dir=output_dir)

    basename_buffered = f"{tilename}_buffer.las"
    basename_filtered = f"{tilename}_filter.las"
    basename_interpolated = f"{tilename}_interp.tif"
    basename_hillshade = f"{tilename}_hillshade.tif"

    file_buffered = os.path.join(output_tree[type_raster.upper()]["buffer"], basename_buffered)
    file_filtered = os.path.join(output_tree[type_raster.upper()]["filter"], basename_filtered)
    raster_dxm_brut = os.path.join(output_tree[type_raster.upper()]["output"], basename_interpolated)
    raster_dxm_hillshade =  os.path.join(output_tree[type_raster.upper()]["hillshade"], basename_hillshade)
    
    # add buffer
    run_pdaltools_buffer(input_dir=input_dir, 
                        tile_filename=input_file,
                        output_filename=file_buffered,
                        buffer_width=config_dict["buffer"]["size"],
                        tile_width=config_dict["tile_geometry"]["tile_width"],
                        tile_coord_scale=config_dict["tile_geometry"]["tile_coord_scale"])
    # filter
    run_mnx_filter_las_classes(
                        input_file=file_buffered,
                        output_file=file_filtered,
                        spatial_reference=config_dict["io"]["spatial_reference"],
                        keep_classes=config_dict["filter"]["keep_classes"][type_raster])

    # interpolate
    run_mnx_interpolation(
                        input_file=file_filtered, 
                        output_raster=raster_dxm_brut, 
                        config=config_dict)

    # add hillshade
    add_hillshade_one_raster(
                        input_raster=raster_dxm_brut,
                        output_raster=raster_dxm_hillshade
    )

    return raster_dxm_hillshade


def create_dxm_with_hillshade_one_las_XM(input_file: str,
                        output_dir: str,
                        config_file=os.path.join("ctview","config.json"),
                        type_raster: str="dtm",
                        pixel_size: float=1.0):
    """Create DXM with hillshade according to a configuration.
    Args :
        input_file : LAS file oin input
        output_dir : output directory
        config_file : json of configuration
        type_raster : can be dtm / dsm / dtm_dens
        pixel_size : precision in meter
    """
    # modif config
    config_dict = utils_tools.convert_json_into_dico(config_file)
    config_dict["tile_geometry"]["pixel_size"] = pixel_size

    # create dtm with hillshade
    raster_dtm_hillshade = create_mnx_one_las(input_file=input_file, output_dir=output_dir, config_dict=config_dict, type_raster=type_raster)

    return raster_dtm_hillshade


def create_dtm_with_hillshade_one_las_5M(input_file: str,
                        output_dir: str):
    """Create DSM with hillshade and fix precision (pixel size) at 5 meters
    """
    output_raster = create_dxm_with_hillshade_one_las_XM(input_file=input_file,
                        output_dir=output_dir,
                        type_raster="dtm_dens",
                        pixel_size=5)
    return output_raster


def create_dtm_with_hillshade_one_las_1M(input_file: str,
                        output_dir: str):
    """Create DTM with hillshade and fix precision (pixel size) at 1 meter
    """
    output_raster = create_dxm_with_hillshade_one_las_XM(input_file=input_file,
                        output_dir=output_dir,
                        type_raster="dtm",
                        pixel_size=1.0)
    return output_raster


def create_dsm_with_hillshade_one_las_50CM(input_file: str,
                        output_dir: str):
    """Create DTM with hillshade and fix precision (pixel size) at 0.5 meter
    """
    output_raster = create_dxm_with_hillshade_one_las_XM(input_file=input_file,
                        output_dir=output_dir,
                        type_raster="dsm",
                        pixel_size=0.5)
    return output_raster


def color_raster_dtm_hillshade_with_LUT(input_initial_basename: str,
                        input_raster: str,
                        output_dir: str,
                        list_c: list,
                        dico_fld: dict):
    """Color a raster according color palette define in a LUT file.
    Args :
        input_initial_file : full path of initial LAS file (use for named the output raster)
        input_raster : input raster to color
        output_dir : output directory
        list_c : the number of cycle that determine how th use the LUT 
    """
    try :
        output_dir_color = output_tree["DTM"]["color"]
    except NameError: # in case tree was not created -> raise "NameError: name 'output_tree' is not defined"
        output_tree = create_output_tree(output_dir=output_dir)
        output_dir_color = output_tree["DTM"]["color"]

    log.info("Build DTM hillshade color")

    cpt = 1

    for cycle in list_c:

        log.info(f"{cpt}/{len(list_c)}...")
        folder_DXM_color = dico_fld[f"folder_DTM_color{cycle}"]
        output_dir_raster = os.path.join(output_dir_color,folder_DXM_color)
        os.makedirs(output_dir_raster, exist_ok=False)

        color_DTM_with_cycles(
            las_input_file=input_initial_basename,
            output_dir_raster=output_dir_raster,
            output_dir_LUT=os.path.join(output_dir, dico_fld["folder_LUT"]),
            raster_DTM_file=input_raster,
            nb_cycle=cycle,
        )

        cpt += 1

    log.info(f"End DTM.\n")


def hillshade_from_raster(input_raster: str, output_raster: str):
    """Add hillshade to raster"""
    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing="hillshade",
    )


def color_DTM_with_cycles(
    las_input_file: str, output_dir_raster: str, output_dir_LUT: str, raster_DTM_file: str, nb_cycle: int
):
    """Color a raster with a LUT created depending of a choice of cycles

    Argss :
        file_las : str : points cloud
        file_DTM : str : DTM corresponding to the points cloud
        nb_cycle : int : the number of cycle that determine the LUT
    """
    log.info("Generate DTM colorised :")
    log.info("(1/2) Generate LUT.")
    # Create LUT
    LUT = gen_LUT_X_cycle.generate_LUT_X_cycle(
        file_las=las_input_file, file_DTM=raster_DTM_file, nb_cycle=nb_cycle, output_dir_LUT=output_dir_LUT
    )

    # Path DTM colorised
    raster_DTM_color_file = os.path.join(
        output_dir_raster,
        f"{os.path.splitext(las_input_file)[0]}_DTM_hillshade_color{nb_cycle}c.tif",
    )

    log.info("DTM color : " + raster_DTM_color_file)
    log.info("(2/2) Colorise raster.")

    # Colorisation
    utils_gdal.color_raster_with_LUT(
        input_raster=raster_DTM_file,
        output_raster=raster_DTM_color_file,
        LUT=LUT,
    )


if __name__ == "__main__":

    main()
