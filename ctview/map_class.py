import logging as log
import os
import tempfile
from typing import Tuple

import hydra
import numpy as np
import laspy
from collections.abc import Iterable
from omegaconf import DictConfig
from osgeo_utils import gdal_fillnodata

from ctview import clip_raster, map_DXM, utils_gdal, utils_pdal, utils_raster


def generate_class_raster_raw(
    input_points: np.array,
    input_classifs: np.array,
    output_tif: str,
    epsg: int | str,
    classes_by_layer: list = [[]],
    tile_size: int = 1000,
    pixel_size: float = 1,
    buffer_size: float = 0,
    no_data_value: int = -9999,
    raster_driver: str = "GTiff",
):
    """Generate a (multilayer) raster of class for the classes in `class_by_layer`.

    The output has one layer per value in the classes_by_layer list.
    Each layer contains a class map for the classes listed in its correspondig list of
    values in classes_by_layer.
    Eg, if classes_by_layer = [[1, 2], [3], []]:
    * the first layer contains the class map for classes 1 and 2 commbined
    * the second layer contains the class map for class 3 only,
    * the last layer contains the class for all classes together

    Args:
        input_points (np.array): numpy array with the input points
        input_classifs (np.array): numpy array with classifications of the input points
        output_tif (str): path to the output file
        epsg (int): spatial reference of the output file
        classes_by_layer (list, optional): _description_. Defaults to [[]].
        tile_size (int, optional): size ot the raster tile in meters. Defaults to 1000.
        pixel_size (float, optional): pixel size of the output raster. Defaults to 1.
        buffer_size (float, optional): size of the buffer that has been added to the input points.
        (used to detect the raster corners) Defaults to 0.
        no_data_value (int, optional): No data value of the output. Defaults to -9999.
        raster_driver (str): raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers). Defaults to "GTiff"
    """

    os.makedirs(os.path.dirname(output_tif), exist_ok=True)
    utils_raster.generate_raster_raw(
        input_points=input_points,
        input_classifs=input_classifs,
        output_tif=output_tif,
        epsg=epsg,
        fn=compute_binary_class,
        classes_by_layer=classes_by_layer,
        tile_size=tile_size,
        pixel_size=pixel_size,
        buffer_size=buffer_size,
        no_data_value=no_data_value,
        raster_driver=raster_driver,
    )


def compute_binary_class(points: np.array, origin: Tuple[int, int], tile_size: int, pixel_size: float):
    bins_x = np.arange(origin[0], origin[0] + tile_size + pixel_size, pixel_size)
    bins_y = np.arange(origin[1] - tile_size, origin[1] + pixel_size, pixel_size)
    # Compute number of points per bin
    bins, _, _ = np.histogram2d(points[:, 1], points[:, 0], bins=[bins_y, bins_x])
    # Get 1 when value is not 0, 0 otherwise
    binary_class = np.where(bins > 0, 1, 0)
    binary_class = np.flipud(binary_class)

    return binary_class


def create_class_raster_raw(
    in_points: np.ndarray, output_file: str, res: int, raster_driver: str, no_data_value: float
):
    """Create raw raster of classes.

    Args:
        input_points (np.array): Points of the input las (as read with a pdal.readers.las)
        output_file (str): full path to the output raster
        res (int): pixel size of the output raster
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)
        no_data_value (float): Value of pixel if contains no data
    Raises:
        FileNotFoundError: if the output raster has not been created
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    utils_pdal.write_raster_class(
        input_points=in_points,
        output_raster=output_file,
        res=res,
        raster_driver=raster_driver,
        no_data_value=no_data_value,
    )

    if not os.path.exists(output_file):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{output_file} not found")


def fill_gaps_raster(in_raster: str, output_file: str, raster_driver: str):
    """Fill gaps on a raster using gdal.

    Args:
        in_raster (str): path to the raster to fill
        output_file (str): full path to the output raster
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)

    Raises:
        FileNotFoundError: if the output raster has not been created
    """

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    gdal_fillnodata.gdal_fillnodata(
        src_filename=in_raster,
        band_number=2,
        dst_filename=output_file,
        driver_name=raster_driver,
        creation_options=None,
        quiet=True,
        mask="default",
        max_distance=2,
        smoothing_iterations=0,
        options=None,
    )

    if not os.path.exists(output_file):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{output_file} not found")


def add_color_to_raster(in_raster: str, output_file: str, LUT: str):
    """Color a raster using method gdal DEMProcessing with a specific LUT.

    Args:
        in_raster (str): path to the input raster (to be colored)
        output_file (str): full path to the output raster
        LUT (str): path to the LUT used to color the raster

    Raises:
        FileNotFoundError: if the output raster has not been created
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    utils_gdal.color_raster_with_LUT(input_raster=in_raster, output_raster=output_file, LUT=LUT)

    if not os.path.exists(output_file):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{output_file} not found")


def create_map_class_raster_with_postprocessing_color_and_hillshade(
    input_las: str,
    tilename: str,
    config_class: DictConfig | dict,
    config_io: DictConfig | dict,
    output_bounds: Tuple,
):
    """Create a raster of class with post processing steps:
    * fill gaps with a method of gdal
    * colorisation
    * mix with a hillshade that comes from an elevation model

    Args:
        input_las (str): path to the input las file
        tilename (str): tilename used to generate the output filename
        config_class (DictConfig | dict):  hydra configuration with the class map parameters
        eg. {
          pixel_size: 0.5  # pixel size of the output raster
          dxm_interpolation: pdal-tin  # interpolation used to generate the hillshade elevation model
          keep_classes: [1, 2, 3, 4]  # classes used in the hillshae elevation model
          lut_filename: LUT_CLASS.txt  # filename for the lut that colorizes the classification map
          output_subdir: CC_6_fusion  # folder name for the final class map output
          hillshade_calc: "254*((A*(0.5*(B/255)+0.25))>254)+(A*(0.5*(B/255)+0.25))*((A*(0.5*(B/255)+0.25))<=254)"
          # formula used to mix the classification map with its hillshade
          intermediate_dirs:  # paths to the saved intermediate results
              CC_raw: CC_1_raw
              CC_raw_color: CC_2_bcolor
              CC_fillgap: CC_3_fg
              CC_fillgap_color: CC_4_fgcolor
              CC_crop: CC_5_crop
              dxm_raw: "DSM"
              dxm_hillshade: "tmp_dsm/hillshade"

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
        output_bounds (Tuple): bounds of the output raster file ([minx,maxx],[miny, maxy]).
            Should correspond to the las input file before adding any buffer
    """
    log.basicConfig(level=log.INFO, format="%(message)s")

    # File names
    input_las_name = os.path.basename(input_las)
    in_points = utils_pdal.read_las_file(input_las)

    log.info(f"\nMAP OF CLASS : file : {input_las_name}")

    # Output_folder_names
    out_dir = config_io.output_dir
    inter_dirs = config_class.intermediate_dirs
    ext = config_io.extension

    with tempfile.TemporaryDirectory(prefix="tmp_class", dir="tmp") as tmpdir:
        if inter_dirs["CC_raw"]:
            raster_raw = os.path.join(out_dir, inter_dirs["CC_raw"], f"{tilename}_raw{ext}")
        else:
            raster_raw = os.path.join(tmpdir, f"{tilename}_raw{ext}")
        if inter_dirs["CC_raw_color"]:
            raster_raw_color = os.path.join(out_dir, inter_dirs["CC_raw_color"], f"{tilename}_raw_color{ext}")

        if inter_dirs["CC_fillgap"]:
            raster_fillgap = os.path.join(out_dir, inter_dirs["CC_fillgap"], f"{tilename}_fillgap{ext}")
        else:
            raster_fillgap = os.path.join(tmpdir, f"{tilename}_fillgap{ext}")
        if inter_dirs["CC_fillgap_color"]:
            raster_fg_color = os.path.join(out_dir, inter_dirs["CC_fillgap_color"], f"{tilename}_fillgap_color{ext}")
        else:
            raster_fg_color = os.path.join(tmpdir, f"{tilename}_fillgaps_color{ext}")
        if inter_dirs["CC_crop"]:
            raster_fg_color_clip = os.path.join(out_dir, inter_dirs["CC_crop"], f"{tilename}_fillgap_color_clip{ext}")
        else:
            raster_fg_color_clip = os.path.join(tmpdir, f"{tilename}_fillgap_color_clip{ext}")

        if inter_dirs.dxm_raw:
            raster_class_map_dxm_raw = os.path.join(out_dir, inter_dirs.dxm_raw, f"{tilename}_interp{ext}")
        else:
            raster_class_map_dxm_raw = os.path.join(tmpdir, f"{tilename}_interp{ext}")
        if inter_dirs.dxm_hillshade:
            raster_class_map_dxm_hs = os.path.join(out_dir, inter_dirs.dxm_hillshade, f"{tilename}_hillshade{ext}")
        else:
            raster_class_map_dxm_hs = os.path.join(tmpdir, f"{tilename}_hillshade{ext}")

        raster_class_map = os.path.join(out_dir, config_class.output_subdir, f"{tilename}_fusion_DSM_class{ext}")
        os.makedirs(os.path.dirname(raster_class_map), exist_ok=True)

        log.info("Step 1 : Write raster raw")
        create_class_raster_raw(
            in_points=in_points,
            output_file=raster_raw,
            res=config_class.pixel_size,
            raster_driver=config_io.raster_driver,
            no_data_value=config_io.no_data_value,
        )

        if inter_dirs["CC_raw_color"]:
            log.info("Step 1.5 : Write raster raw colorized")
            add_color_to_raster(
                in_raster=raster_raw,
                output_file=raster_raw_color,
                LUT=os.path.join(config_io.lut_folder, config_class.lut_filename),
            )

        log.info("Step 2 : Write raster with fillgap")
        fill_gaps_raster(
            in_raster=raster_raw,
            output_file=raster_fillgap,
            raster_driver=config_io.raster_driver,
        )

        log.info("Step 2 : Write raster with fillgap and color")
        add_color_to_raster(
            in_raster=raster_fillgap,
            output_file=raster_fg_color,
            LUT=os.path.join(config_io.lut_folder, config_class.lut_filename),
        )
        log.info("Step 3 : Write raster with fillgap, color + clipped at the right bounds")
        clip_raster.clip_raster(
            input_raster=raster_fg_color,
            output_raster=raster_fg_color_clip,
            bounds=output_bounds,
            raster_driver=config_io.raster_driver,
        )

        map_DXM.add_dxm_hillshade_to_raster(
            input_raster=raster_fg_color_clip,
            input_pointcloud=str(input_las),
            output_raster=raster_class_map,
            pixel_size=config_class.pixel_size,
            keep_classes=config_class.keep_classes,
            dxm_interpolation=config_class.dxm_interpolation,
            output_dxm_raw=raster_class_map_dxm_raw,
            output_dxm_hillshade=raster_class_map_dxm_hs,
            hillshade_calc=config_class.hillshade_calc,
            config_io=config_io,
        )


@hydra.main(config_path="../configs/", config_name="config_ctview.yaml", version_base="1.2")
def main(config: DictConfig):
    log.basicConfig(level=log.INFO, format="%(message)s")
    initial_las_file = os.path.join(config.io.input_dir, config.io.input_filename)
    las_bounds = utils_pdal.get_bounds_from_las(initial_las_file)
    os.makedirs(config.io.output_dir, exist_ok=True)
    create_map_class_raster_with_postprocessing_color_and_hillshade(
        input_las=initial_las_file,
        tilename=os.path.splitext(os.path.basename(initial_las_file))[0],
        config_class=config.class_map,
        config_io=config.io,
        output_bounds=las_bounds,
    )
    log.info("END.")


if __name__ == "__main__":
    main()
