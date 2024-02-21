import logging as log
import os
from typing import List

import produits_derives_lidar.ip_one_tile
from omegaconf import DictConfig
from osgeo_utils import gdal_calc

from ctview import add_color, add_hillshade


def create_raw_dxm(
    input_file: str,
    output_dxm: str,
    pixel_size: int,
    dxm_interpolation: str,
    keep_classes: List[int],
    config_io: DictConfig,
):
    """Create a Digital Model (DSM or DTM) with the classes listed in `keep_classes` using the produits_derives_lidar
    library

    WARNING: the dtm bounds are infered from the filename inside the produits_derives_lidar library
    (dtm is not computed on the potential additional buffer)

    Args:
        input_file (str): Patht o the input file
        output_dxm (str): path to the output digital model raster
        pixel_size (int): pixel size of the output raster
        dxm_interpolation (str):  interpolation method for the generated dsm/dtm
        (see available methods in produits_derives_lidar)
        keep_classes (List[int]): classes to keep in the generated digital model
        config (DictConfig): general ctview configuration dictionary the must contain:
            "spatial_reference": #str,
            "no_data_value": #int,
            "tile_geometry": {
                "tile_coord_scale": #int,
                "tile_width": #int,
              }
        cf. configs/config_ctview.yaml for an example.
        The config will be completed with pixel_size, keep_classes and dxm_interpolation
        to match produits_derive_lidar configuration expectations
    """

    # Generate config that suits for produits_derive_lidar interpolation
    pdl_config = {}
    pdl_config["io"] = {"spatial_reference": config_io.spatial_reference}
    pdl_config["tile_geometry"] = dict(config_io.tile_geometry)
    pdl_config["tile_geometry"]["pixel_size"] = pixel_size
    pdl_config["tile_geometry"]["no_data_value"] = config_io.no_data_value
    pdl_config["interpolation"] = {"algo_name": dxm_interpolation}
    pdl_config["filter"] = {"keep_classes": keep_classes}
    log.debug("Config for dxm generation")
    log.debug(pdl_config)

    produits_derives_lidar.ip_one_tile.interpolate(input_file=input_file, output_raster=output_dxm, config=pdl_config)


def add_dxm_hillshade_to_raster(
    input_raster: str,
    input_pointcloud: str,
    output_raster: str,
    pixel_size: float,
    keep_classes: List,
    dxm_interpolation: str,
    output_dxm_raw: str,
    output_dxm_hillshade: str,
    hillshade_calc: str,
    config_io: DictConfig,
):
    """Add hillshade to a raster by computing a Digital Model with the classes listed in keep_classes,
    hillshading it then mixing it with the input raster using the hillshade_calc operation in gdal_calc

    Args:
        input_raster (str): Path to the raster to which we want to add a hillshade
        input_pointcloud (str): Path to the las file used to generate the hillshade
        output_raster (str): Path to the raster output
        pixel_size (float): output pixel size of the generated dsm/dtm
        keep_classes (List): classes to keep in the generated dsm/dtm
        dxm_interpolation (str): interpolation method for the generated dsm/dtm
        (see available methods in produits_derives_lidar)
        output_dxm_raw (str): Path to raw digital model (intermediate result)
        output_dxm_hillshade (str):  Path to hillshade model (intermediate result)
        hillshade_calc (str): Formula used by gdalcalc to mix the raster and its hillshade
        (with A: input_raster, B: hillshade)
        config_io (DictConfig): configuration dictionary the must contain:
            "spatial_reference": #str,
            "no_data_value": #int,
            "tile_geometry": {
                "tile_coord_scale": #int,
                "tile_width": #int,
              }
        cf. configs/config_ctview.yaml for an example ("io" subdivision)
        The config will be completed with pixel_size, keep_classes and dxm_interpolation
        to match produits_derive_lidar configuration expectations
    """
    os.makedirs(os.path.dirname(output_dxm_raw), exist_ok=True)
    os.makedirs(os.path.dirname(output_dxm_hillshade), exist_ok=True)
    os.makedirs(os.path.dirname(output_raster), exist_ok=True)

    create_raw_dxm(input_pointcloud, output_dxm_raw, pixel_size, dxm_interpolation, keep_classes, config_io)
    add_hillshade.add_hillshade_one_raster(input_raster=output_dxm_raw, output_raster=output_dxm_hillshade)

    gdal_calc.Calc(
        A=input_raster,
        B=output_dxm_hillshade,
        calc=hillshade_calc,
        outfile=output_raster,
        allBands="A",
        overwrite=True,
        NoDataValue=config_io.no_data_value,
    )


def create_colored_dxm_with_hillshade(
    input_las: str,
    tilename: str,
    config_dtm: DictConfig | dict,
    config_io: DictConfig | dict,
):
    """Create a DTM or a DSM from a las tile and a configuration

    Args:
        input_las (str): full path of LAS/LAZ file
        tilename (str): tilename used to generate the output filename
        config_dtm (DictConfig | dict): hydra configuration with the dtm parameters
        eg. {
          pixel_size: 1  # Pixel size of the output raster
          keep_classes: [2, 66]  # List of classes to use in the elevation model
          dxm_interpolation: pdal-tin  # Interpolation method for the elevation model
          color:
              cycles_DTM_colored: [1]  # List of numbers of LUT cycles for the colorisation
                                       # (one raster is generated for each value)
              folder_LUT: "LUT"  # Output subfolder for the output LUTs
          output_subdir: "DTM/color"  # Output subfolder for the final dtm output
          intermediate_dirs:  # paths to the saved intermediate results
            dxm_raw: "DTM"
            dxm_hillshade: "tmp_dtm/hillshade"

        }
        config_io (DictConfig | dict): hydra configuration with the general io parameters
        eg.  {
            input_filename: null
            input_dir: null
            output_dir: null
            spatial_reference: EPSG:2154
            lut_folder: LUT
            extension: .tif
            raster_driver: GTiff
            no_data_value: -9999
            tile_geometry:
                tile_coord_scale: 1000
                tile_width: 1000
            }
    """
    out_dir = config_io.output_dir
    inter_dirs = config_dtm.intermediate_dirs
    ext = config_io.extension

    # prepare outputs
    raster_dtm_dxm_raw = os.path.join(out_dir, inter_dirs.dxm_raw, f"{tilename}_interp{ext}")
    raster_dtm_dxm_hillshade = os.path.join(out_dir, inter_dirs.dxm_hillshade, f"{tilename}_hillshade{ext}")

    dir_dtm_colored = os.path.join(out_dir, config_dtm.output_subdir)
    dir_dtm_lut = os.path.join(out_dir, config_dtm.color.folder_LUT)

    os.makedirs(os.path.dirname(raster_dtm_dxm_raw), exist_ok=True)
    os.makedirs(os.path.dirname(raster_dtm_dxm_hillshade), exist_ok=True)

    create_raw_dxm(
        input_las,
        raster_dtm_dxm_raw,
        config_dtm.pixel_size,
        config_dtm.dxm_interpolation,
        config_dtm.keep_classes,
        config_io,
    )

    # add hillshade
    add_hillshade.add_hillshade_one_raster(input_raster=raster_dtm_dxm_raw, output_raster=raster_dtm_dxm_hillshade)

    add_color.color_raster_dtm_hillshade_with_LUT(
        input_initial_basename=os.path.basename(input_las),
        input_raster=raster_dtm_dxm_hillshade,
        output_dir=dir_dtm_colored,
        list_c=config_dtm.color.cycles_DTM_colored,
        output_dir_LUT=dir_dtm_lut,
    )
