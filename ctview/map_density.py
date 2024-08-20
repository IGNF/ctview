import logging as log
import os
import tempfile
from collections.abc import Iterable
from typing import Tuple

import laspy
import numpy as np
from omegaconf import DictConfig

from ctview import add_color, utils_raster


def generate_raster_of_density(
    input_points: np.array,
    input_classifs: np.array,
    output_tif: str,
    epsg: int | str,
    raster_origin: tuple,
    classes_by_layer: list = [[]],
    tile_width: int = 1000,
    pixel_size: float = 1,
    no_data_value: int = -9999,
    raster_driver: str = "GTiff",
):
    """Generate a (multilayer) raster of density for the classes in `class_by_layer`.

    The output has one layer per value in the classes_by_layer list.
    Each layer contains a density map for the classes listed in its correspondig list of
    values in classes_by_layer.
    Eg, if classes_by_layer = [[1, 2], [3], []]:
    * the first layer contains the density map for classes 1 and 2 commbined
    * the second layer contains the density map for class 3 only,
    * the last layer contains the density for all classes together

    Args:
        input_points (np.array): numpy array with the input points
        input_classifs (np.array): numpy array with classifications of the input points
        output_tif (str): path to the output file
        epsg (int): spatial reference of the output file
        raster_origin (tuple): origin of the output raster
        classes_by_layer (list, optional): _description_. Defaults to [[]].
        tile_width (int, optional): size ot the raster tile in meters. Defaults to 1000.
        pixel_size (float, optional): pixel size of the output raster. Defaults to 1.
        no_data_value (int, optional): No data value of the output. Defaults to -9999.
        raster_driver (str): raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers). Defaults to "GTiff"
    """
    utils_raster.generate_raster_raw(
        input_points=input_points,
        input_classifs=input_classifs,
        output_tif=output_tif,
        epsg=epsg,
        raster_origin=raster_origin,
        fn=compute_density,
        classes_by_layer=classes_by_layer,
        tile_width=tile_width,
        pixel_size=pixel_size,
        no_data_value=no_data_value,
        raster_driver=raster_driver,
    )


def compute_density(points: np.array, origin: Tuple[int, int], tile_width: int, pixel_size: float):
    # Compute number of points per bin
    bins_x = np.arange(origin[0], origin[0] + tile_width + pixel_size, pixel_size)
    bins_y = np.arange(origin[1] - tile_width, origin[1] + pixel_size, pixel_size)
    bins, _, _ = np.histogram2d(points[:, 1], points[:, 0], bins=[bins_y, bins_x])
    density = bins / (pixel_size**2)
    density = np.flipud(density)

    return density


def create_density_raster_from_config(
    input_las: str, tilename: str, config_density: DictConfig | dict, config_io: DictConfig | dict, buffer_size: float
) -> str:
    """Generate density raster:
    * colored with lut provided in config_density
    * mixed with hillshade from digital elevation model using a formula given in config_density

    Args:
        input_las (str): path to the input las file
        tilename (str): tilename used to generate the output filename
        config_density (DictConfig | dict): hydra configuration with the density parameters
        eg.  {
            pixel_size: 5
            keep_classes: [2, 66]
            dxm_filter:  # Filter used to generate dtm
                dimension: Classification
                keep_values: [2, 66]
            lut_filename: LUT_DENSITY.txt
            output_subdir: DENS_FINAL
            intermediate_dirs:
                density_values: DENS_VAL
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
        buffer_size (float): size of the buffer that has been added to the las file
        (used to create a raster without buffer)

    Raises:
        TypeError: if config_density.keep_classes does not have the correct type

    Returns:
        str: path to the output raster
    """

    log.info("\nCreate density maps")
    out_dir = config_io.output_dir
    inter_dirs = config_density.get("intermediate_dirs", "")
    ext = config_io.extension

    if not isinstance(config_density.keep_classes, Iterable):
        raise TypeError(
            "In create_colored_density_raster, "
            "config_density.keep_classes is expected to be a list, "
            f"got {type(config_density.keep_classes)} instead)"
        )
    if not np.all([isinstance(item, Iterable) for item in config_density["keep_classes"]]):
        raise TypeError(
            "In create_colored_density_raster, "
            "config_density.keep_classes is expected to be a list of lists "
            "(with the classes to keep on each band of the output raster), "
            f"got {config_density['keep_classes']} instead)"
        )
    if config_density["colorize"] and (len(config_density["keep_classes"]) != 1):
        raise ValueError(
            "In create_colored_density_raster, config_density['keep_classes'] should describe only 1 band"
            "if colorize = True,  "
            f"got {config_density['keep_classes']} instead)"
        )

    with tempfile.TemporaryDirectory(prefix="tmp_density", dir="tmp") as tmpdir:
        raster_dens = os.path.join(out_dir, config_density.output_subdir, f"{tilename}_density{ext}")

        if config_density["colorize"]:
            if inter_dirs and inter_dirs.density_values:
                raster_dens_values = os.path.join(out_dir, inter_dirs.density_values, f"{tilename}_density{ext}")
            else:
                raster_dens_values = os.path.join(tmpdir, f"{tilename}_density{ext}")
        else:
            raster_dens_values = raster_dens

        os.makedirs(os.path.dirname(raster_dens_values), exist_ok=True)
        os.makedirs(os.path.dirname(raster_dens), exist_ok=True)

        log.info("\nRead point cloud\n")
        las = laspy.read(input_las)
        points_np = np.vstack((las.x, las.y, las.z)).transpose()
        classifs = np.copy(las.classification)

        log.info("\nCreate density map (values)\n")
        raster_origin = utils_raster.compute_raster_origin(
            input_points=points_np,
            tile_width=config_io.tile_geometry.tile_width,
            pixel_size=config_density.pixel_size,
            buffer_size=buffer_size,
        )

        generate_raster_of_density(
            input_points=points_np,
            input_classifs=classifs,
            output_tif=raster_dens_values,
            epsg=config_io.spatial_reference,
            raster_origin=raster_origin,
            classes_by_layer=config_density.keep_classes,
            tile_width=config_io.tile_geometry.tile_width,
            pixel_size=config_density.pixel_size,
            no_data_value=config_io.no_data_value,
            raster_driver=config_io.raster_driver,
        )

        if config_density["colorize"]:
            log.info("\nColorize density map\n")
            add_color.color_raster_with_interpolation(
                input_raster=raster_dens_values,
                output_raster=raster_dens,
                colormap=config_density.colormap,
            )

    return raster_dens
