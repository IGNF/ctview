import logging as log
import os
from typing import Tuple

import hydra
import numpy as np
from omegaconf import DictConfig
from osgeo_utils import gdal_fillnodata

from ctview import clip_raster, map_DXM, utils_gdal, utils_pdal


def step1_create_raster_brut(
    in_points: np.ndarray,
    output_dir: str,
    output_filename: str,
    output_extension: str,
    res: int,
    i: int,
    raster_driver: str,
) -> str:
    """Create raw raster of classes.

    Args:
        input_points (np.array): Points of the input las (as read with a pdal.readers.las)
        output_dir (str): path to the output raster directory
        output_filename (_type_): name of output file whithout extension
        output_extension (str): extension of output file
        res (int): pixel size of the output raster
        i (int): step index (for logging)
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)

    Raises:
        FileNotFoundError: if the output raster has not been created

    Returns:
        str: Full path to the output filled raster
    """
    os.makedirs(output_dir, exist_ok=True)
    raster_brut = os.path.join(output_dir, f"{output_filename}_raster{output_extension}")
    log.info(f"Step {i}/4 : Raster of class brut : {raster_brut}")
    utils_pdal.write_raster_class(
        input_points=in_points, output_raster=raster_brut, res=res, raster_driver=raster_driver
    )

    if not os.path.exists(raster_brut):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{raster_brut} not found")

    return raster_brut


def step2_create_raster_fillgap(
    in_raster: str, output_dir: str, output_filename, output_extension: str, i: int, raster_driver: str
) -> str:
    """Fill gaps on a raster using gdal.

    Args:
        in_raster (str): path to the raster to fill
        output_dir (str): path to the output raster directory
        output_filename (_type_): name of output file whithout extension
        output_extension (str): extension of output file
        i (int): step index (for logging)
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)

    Raises:
        FileNotFoundError: if the output raster has not been created

    Returns:
        str: Full path to the output filled raster
    """

    os.makedirs(output_dir, exist_ok=True)
    fillgap_raster = os.path.join(output_dir, f"{output_filename}_raster_fillgap{output_extension}")
    log.info(f"Step {i}/4 : Fill gaps : {fillgap_raster}")
    gdal_fillnodata.gdal_fillnodata(
        src_filename=in_raster,
        band_number=2,
        dst_filename=fillgap_raster,
        driver_name=raster_driver,
        creation_options=None,
        quiet=True,
        mask="default",
        max_distance=2,
        smoothing_iterations=0,
        options=None,
    )

    if not os.path.exists(fillgap_raster):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{fillgap_raster} not found")

    return fillgap_raster


def step3_color_raster(
    in_raster: str, output_dir: str, tilename: str, output_extension: str, verbose: str, i: int, LUT: str
) -> str:
    """Color a raster using method gdal DEMProcessing with a specific LUT.

    Args:
        in_raster (str): path to the input raster (to be colored)
        output_dir (str): path to the output directory
        tilename (str): name of the tile (usually las filename without extension, used to generate an output filename)
        output_extension (str): extension of the output file
        verbose (str):  suffix for the output filename
        i (int): index of the step, used for logging
        LUT (str): path to the LUT used to color the raster

    Raises:
        FileNotFoundError: if the output raster has not been created

    Returns:
        str: Full path of colored raster
    """
    os.makedirs(output_dir, exist_ok=True)
    raster_colored = os.path.join(output_dir, f"{tilename}_{verbose}{output_extension}")
    log.info(f"Step {i}/4 : {verbose} : {raster_colored}")

    utils_gdal.color_raster_with_LUT(input_raster=in_raster, output_raster=raster_colored, LUT=LUT)

    if not os.path.exists(raster_colored):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{raster_colored} not found")

    return raster_colored


def create_map_class_raster_with_postprocessing_color_and_hillshade(
    input_las: str,
    tilename: str,
    config_class: DictConfig | dict,
    config_io: DictConfig | dict,
    output_bounds: Tuple,
) -> str:
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
              CC_brut: CC_1_brut
              CC_brut_color: CC_2_bcolor
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


    Returns:
        str: Full path of raster filled, colorised and mixed with hillshade
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
    output_folder_1 = os.path.join(out_dir, inter_dirs["CC_brut"])
    output_folder_2 = os.path.join(out_dir, inter_dirs["CC_brut_color"])
    output_folder_3 = os.path.join(out_dir, inter_dirs["CC_fillgap"])
    output_folder_4 = os.path.join(out_dir, inter_dirs["CC_fillgap_color"])
    output_folder_5 = os.path.join(out_dir, inter_dirs["CC_crop"])

    # prepare outputs
    raster_class_map_dxm_raw = os.path.join(out_dir, inter_dirs.dxm_raw, f"{tilename}_interp{ext}")
    raster_class_map_dxm_hillshade = os.path.join(out_dir, inter_dirs.dxm_hillshade, f"{tilename}_hillshade{ext}")
    raster_class_map = os.path.join(out_dir, config_class.output_subdir, f"{tilename}_fusion_DSM_class{ext}")
    os.makedirs(os.path.dirname(raster_class_map), exist_ok=True)

    # Step 1 : Write raster brut
    raster_brut = step1_create_raster_brut(
        in_points=in_points,
        output_dir=output_folder_1,
        output_filename=tilename,
        res=config_class.pixel_size,
        i=1,
        output_extension=ext,
        raster_driver=config_io.raster_driver,
    )

    # Step 2 : Color brut
    step3_color_raster(
        in_raster=raster_brut,
        output_dir=output_folder_2,
        tilename=tilename,
        output_extension=ext,
        verbose="raster_color",
        i=2,
        LUT=os.path.join(config_io.lut_folder, config_class.lut_filename),
    )

    # Step 3 :  Fill gaps
    fillgap_raster = step2_create_raster_fillgap(
        in_raster=raster_brut,
        output_dir=output_folder_3,
        output_filename=tilename,
        output_extension=ext,
        i=3,
        raster_driver=config_io.raster_driver,
    )

    # Step 4 : Color fill gaps
    color_fillgap_raster = step3_color_raster(
        in_raster=fillgap_raster,
        output_dir=output_folder_4,
        tilename=tilename,
        output_extension=ext,
        verbose="raster_fillgap_color",
        i=4,
        LUT=os.path.join(config_io.lut_folder, config_class.lut_filename),
    )
    # Step 5: Crop
    os.makedirs(output_folder_5, exist_ok=True)
    output_clip_raster = os.path.join(output_folder_5, f"{tilename}_raster{ext}")
    clip_raster.clip_raster(
        input_raster=color_fillgap_raster,
        output_raster=output_clip_raster,
        bounds=output_bounds,
        raster_driver=config_io.raster_driver,
    )

    map_DXM.add_dxm_hillshade_to_raster(
        input_raster=output_clip_raster,
        input_pointcloud=str(input_las),
        output_raster=raster_class_map,
        pixel_size=config_class.pixel_size,
        keep_classes=config_class.keep_classes,
        dxm_interpolation=config_class.dxm_interpolation,
        output_dxm_raw=raster_class_map_dxm_raw,
        output_dxm_hillshade=raster_class_map_dxm_hillshade,
        hillshade_calc=config_class.hillshade_calc,
        config_io=config_io,
    )

    return raster_class_map


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
