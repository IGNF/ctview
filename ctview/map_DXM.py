import os

import produits_derives_lidar.ip_one_tile
from omegaconf import DictConfig

import ctview.add_buffer as add_buffer
import ctview.add_hillshade as add_hillshade


def create_output_tree(output_dir: str):
    """Create tree for output."""
    output_tree = {
        "DTM": {
            "output": os.path.join(output_dir, "DTM"),
            "buffer": os.path.join(output_dir, "tmp_dtm", "buffer"),
            "hillshade": os.path.join(output_dir, "tmp_dtm", "hillshade"),
            "color": os.path.join(output_dir, "DTM", "color"),
        },
        "DSM": {
            "output": os.path.join(output_dir, "DSM"),
            "buffer": os.path.join(output_dir, "tmp_dsm", "buffer"),
            "hillshade": os.path.join(output_dir, "tmp_dsm", "hillshade"),
        },
        "DTM_DENS": {
            "output": os.path.join(output_dir, "DTM_DENS"),
            "buffer": os.path.join(output_dir, "tmp_dtm_dens", "buffer"),
            "hillshade": os.path.join(output_dir, "tmp_dtm_dens", "hillshade"),
        },
    }

    for n in output_tree:
        os.makedirs(output_tree[n]["output"], exist_ok=True)
        os.makedirs(output_tree[n]["buffer"], exist_ok=True)
        os.makedirs(output_tree[n]["hillshade"], exist_ok=True)
    os.makedirs(output_tree["DTM"]["color"], exist_ok=True)

    return output_tree


def create_mnx_one_las(input_file: str, output_dir: str, config: DictConfig, type_raster="dtm"):
    """
    Create a DTM or a DSM from a las tile.
    Args :
        input_file : full path of LAS/LAZ file
        config :  dictionary that must contain
                { "tile_geometry": { "tile_coord_scale": #int,
                                    "tile_width": #int,
                                    "pixel_size": #float,
                                    "no_data_value": #int },
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
    basename_interpolated = f"{tilename}_interp.tif"
    basename_hillshade = f"{tilename}_hillshade.tif"

    file_buffered = os.path.join(output_tree[type_raster.upper()]["buffer"], basename_buffered)
    raster_dxm_brut = os.path.join(output_tree[type_raster.upper()]["output"], basename_interpolated)
    raster_dxm_hillshade = os.path.join(output_tree[type_raster.upper()]["hillshade"], basename_hillshade)

    # add buffer
    add_buffer.run_pdaltools_buffer(
        input_dir=input_dir,
        tile_filename=input_file,
        output_filename=file_buffered,
        buffer_width=config.buffer.size,
        tile_width=config.tile_geometry.tile_width,
        tile_coord_scale=config.tile_geometry.tile_coord_scale,
        spatial_ref=config.io.spatial_reference,
    )

    # filter & interpolate
    # WARNING: config must correspond to ign-mnx:1.0.0
    # config must contain
    # { "tile_geometry": { "tile_coord_scale": #int,
    #                                 "tile_width": #int,
    #                                 "pixel_size": #float,
    #                                 "no_data_value": #int },
    #               "io": { "spatial_reference": #str},
    #               "interpolation": { "algo_name": #str }
    #             }
    #         with
    #             tile_coord_scale value(int): coords in tile names are in km
    #             tile_width value(int): tile width in meters
    #             pixel_size value(float): pixel size for raster generation
    #             spatial_ref value(str): spatial reference to use when reading las file
    #             interpolation_method value(str): interpolation method for raster generation
    produits_derives_lidar.ip_one_tile.interpolate(input_file=input_file, output_raster=raster_dxm_brut, config=config)

    # add hillshade
    add_hillshade.add_hillshade_one_raster(input_raster=raster_dxm_brut, output_raster=raster_dxm_hillshade)

    return raster_dxm_hillshade


def create_dxm_with_hillshade_one_las_XM(
    input_file: str, output_dir: str, config: DictConfig, type_raster: str = "dtm"
):
    """Create DXM with hillshade according to a configuration.
    Args :
        input_file : LAS file oin input
        output_dir : output directory
        config : config hydra
    """

    # create dtm with hillshade
    raster_dtm_hillshade = create_mnx_one_las(
        input_file=input_file, output_dir=output_dir, config=config, type_raster=type_raster
    )

    return raster_dtm_hillshade
