import logging as log
import os
from typing import List

import produits_derives_lidar.ip_one_tile
from omegaconf import DictConfig

import ctview.add_hillshade as add_hillshade


def create_output_tree(output_dir: str):
    """Create tree for output."""
    output_tree = {
        "DTM": {
            "output": os.path.join(output_dir, "DTM"),
            "hillshade": os.path.join(output_dir, "tmp_dtm", "hillshade"),
            "color": os.path.join(output_dir, "DTM", "color"),
        },
        "DSM": {
            "output": os.path.join(output_dir, "DSM"),
            "hillshade": os.path.join(output_dir, "tmp_dsm", "hillshade"),
        },
        "DTM_DENS": {
            "output": os.path.join(output_dir, "DTM_DENS"),
            "hillshade": os.path.join(output_dir, "tmp_dtm_dens", "hillshade"),
        },
    }

    for n in output_tree:
        os.makedirs(output_tree[n]["output"], exist_ok=True)
        os.makedirs(output_tree[n]["hillshade"], exist_ok=True)
    os.makedirs(output_tree["DTM"]["color"], exist_ok=True)

    return output_tree


def create_dxm_with_hillshade_one_las(
    input_file: str,
    output_dir: str,
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

    # manage paths
    _, input_basename = os.path.split(input_file)
    tilename, _ = os.path.splitext(input_basename)

    # prepare outputs
    output_tree = create_output_tree(output_dir=output_dir)

    basename_interpolated = f"{tilename}_interp.tif"
    basename_hillshade = f"{tilename}_hillshade.tif"

    raster_dxm_brut = os.path.join(output_tree[type_raster.upper()]["output"], basename_interpolated)
    raster_dxm_hillshade = os.path.join(output_tree[type_raster.upper()]["hillshade"], basename_hillshade)

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
        input_file=input_file, output_raster=raster_dxm_brut, config=pdl_config
    )

    # add hillshade
    add_hillshade.add_hillshade_one_raster(input_raster=raster_dxm_brut, output_raster=raster_dxm_hillshade)

    return raster_dxm_hillshade
