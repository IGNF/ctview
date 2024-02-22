import logging as log
import os
from typing import List

import produits_derives_lidar.ip_one_tile
from omegaconf import DictConfig

import ctview.add_hillshade as add_hillshade


def create_dxm_with_hillshade_one_las(
    input_file: str,
    output_dxm_raw: str,
    output_dxm_hillshade: str,
    pixel_size: float,
    keep_classes: List,
    dxm_interpolation: str,
    config: DictConfig,
    type_raster="dtm",
) -> str:
    """Create a DTM or a DSM from a las tile and a configuration

    Args:
        input_file (str): full path of LAS/LAZ file
        output_dir (str): output directory
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
        The config with be completed with pixel_size, keep_classes and dxm_interpolation
        to match produits_derive_lidar configuration expectations

        type_raster (str, optional): can be dtm / dsm / dtm_dens. Defaults to "dtm".

    Returns:
        str: path to the output raster
    """

    os.makedirs(os.path.dirname(output_dxm_raw), exist_ok=True)
    os.makedirs(os.path.dirname(output_dxm_hillshade), exist_ok=True)

    # Generate config that suits for produits_derive_lidar interpolation
    pdl_config = {}
    pdl_config["io"] = dict(config.io)
    pdl_config["tile_geometry"] = dict(config.tile_geometry)
    pdl_config["tile_geometry"]["pixel_size"] = pixel_size
    pdl_config["interpolation"] = {"algo_name": dxm_interpolation}
    pdl_config["filter"] = {"keep_classes": keep_classes}
    log.debug(f"Config for {type_raster} raster generation")
    log.debug(pdl_config)

    produits_derives_lidar.ip_one_tile.interpolate(
        input_file=input_file, output_raster=output_dxm_raw, config=pdl_config
    )

    # add hillshade
    add_hillshade.add_hillshade_one_raster(input_raster=output_dxm_raw, output_raster=output_dxm_hillshade)
