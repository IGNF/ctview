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
    config: DictConfig,
):
    """Create a Digital Model (DSM or DTM) with the classes listed in `keep_classes` using the produits_derives_lidar
    library

    Args:
        input_file (str): Patht o the input file
        output_dxm (str): path to the output digital model raster
        pixel_size (int): pixel size of the output raster
        dxm_interpolation (str):  interpolation method for the generated dsm/dtm
        (see available methods in produits_derives_lidar)
        keep_classes (List[int]): classes to keep in the generated digital model
        config (DictConfig): general ctview configuration dictionary the must contain:
            "tile_geometry": {
                "tile_coord_scale": #int,
                "tile_width": #int,
                "no_data_value": #int,
            "io": {
                "spatial_reference": #str},
        cf. configs/config_ctview.yaml for an example.
        The config will be completed with pixel_size, keep_classes and dxm_interpolation
        to match produits_derive_lidar configuration expectations
    """

    # Generate config that suits for produits_derive_lidar interpolation
    pdl_config = {}
    pdl_config["io"] = dict(config.io)
    pdl_config["tile_geometry"] = dict(config.tile_geometry)
    pdl_config["tile_geometry"]["pixel_size"] = pixel_size
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
    config: DictConfig,
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
        config (DictConfig): general ctview configuration dictionary the must contain:
            "tile_geometry": {
                "tile_coord_scale": #int,
                "tile_width": #int,
                "no_data_value": #int,
            "io": {
                "spatial_reference": #str},
        cf. configs/config_ctview.yaml for an example.
        The config will be completed with pixel_size, keep_classes and dxm_interpolation
        to match produits_derive_lidar configuration expectations
    """
    os.makedirs(os.path.dirname(output_dxm_raw), exist_ok=True)
    os.makedirs(os.path.dirname(output_dxm_hillshade), exist_ok=True)
    os.makedirs(os.path.dirname(output_raster), exist_ok=True)

    create_raw_dxm(input_pointcloud, output_dxm_raw, pixel_size, dxm_interpolation, keep_classes, config)
    add_hillshade.add_hillshade_one_raster(input_raster=output_dxm_raw, output_raster=output_dxm_hillshade)

    gdal_calc.Calc(
        A=input_raster,
        B=output_dxm_hillshade,
        calc=hillshade_calc,
        outfile=output_raster,
        allBands="A",
        overwrite=True,
        NoDataValue=config.tile_geometry.no_data_value,
    )


def create_colored_dxm_with_hillshade(
    input_file: str,
    output_dir: str,
    output_dir_LUT: str,
    output_dxm_raw: str,
    output_dxm_hillshade: str,
    color_cycles: List[int],
    pixel_size: float,
    keep_classes: List,
    dxm_interpolation: str,
    config: DictConfig,
):
    """Create a DTM or a DSM from a las tile and a configuration

    Args:
        input_file (str): full path of LAS/LAZ file
        output_dir (str): output directory
            output_dir_LUT (str):  Path to output color lut
        output_dxm_raw (str): Path to raw digital model (intermediate result)
        output_dxm_hillshade (str):  Path to hillshade model (intermediate result)
        color_cycles (List[int]): the number of cycles that determines how th use the LUT,
        one colored digital model is generated for each value of the list
        pixel_size (float): output pixel size of the generated dsm/dtm
        keep_classes (List): classes to keep in the generated dsm/dtm
        dxm_interpolation (str): interpolation method for the generated dsm/dtm
        (see available methods in produits_derives_lidar)
        config (DictConfig): general ctview configuration dictionary the must contain:
            "tile_geometry": {
                "tile_coord_scale": #int,
                "tile_width": #int,
                "no_data_value": #int,
            "io": {
                "spatial_reference": #str},
        cf. configs/config_ctview.yaml for an example.
        The config will be completed with pixel_size, keep_classes and dxm_interpolation
        to match produits_derive_lidar configuration expectations

    """
    os.makedirs(os.path.dirname(output_dxm_raw), exist_ok=True)
    os.makedirs(os.path.dirname(output_dxm_hillshade), exist_ok=True)

    create_raw_dxm(input_file, output_dxm_raw, pixel_size, dxm_interpolation, keep_classes, config)

    # add hillshade
    add_hillshade.add_hillshade_one_raster(input_raster=output_dxm_raw, output_raster=output_dxm_hillshade)

    add_color.color_raster_dtm_hillshade_with_LUT(
        input_initial_basename=os.path.basename(input_file),
        input_raster=output_dxm_hillshade,
        output_dir=output_dir,
        list_c=color_cycles,
        output_dir_LUT=output_dir_LUT,
    )
