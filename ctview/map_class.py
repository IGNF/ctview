import logging as log
import os
from typing import Tuple

import hydra
import numpy as np
from omegaconf import DictConfig
from osgeo_utils import gdal_fillnodata

import ctview.clip_raster as clip_raster
import ctview.utils_gdal as utils_gdal
import ctview.utils_pdal as utils_pdal


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


def create_map_class(
    input_las: str,
    output_dir: str,
    pixel_size: float,
    output_bounds: Tuple,
    extension: str,
    config_intermediate_dirs: DictConfig,
    LUT: str,
    raster_driver: str,
) -> str:
    """Create a raster of class with the fill gaps method of gdal and a colorisation.

    Args:
        input_las (str): path to input las file
        output_dir (str): output directory
        pixel_size (float):  output pixel size of the generated map
        output_bounds (Tuple): bounds of the output raster file ([minx,maxx],[miny, maxy]).
            Should correspond to the las input file before adding any buffer
        extension (str):  output files extension
        config_intermediate_dirs (DictConfig): dictionary that contains path to all the intermediate directories.
            Expected keys are {"CC_brut", "CC_brut_color", "CC_fillgap", "CC_fillgap_color"}
        LUT (str): path to the LUT used to color the raster
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)

    Returns:
        str: Full path of raster filled and colorised
    """
    log.basicConfig(level=log.INFO, format="%(message)s")

    # File names
    input_las_name = os.path.basename(input_las)
    input_las_name_without_extension = os.path.splitext(input_las_name)[0]  # Read las
    in_points = utils_pdal.read_las_file(input_las)

    log.info(f"\nMAP OF CLASS : file : {input_las_name}")

    # Output_folder_names
    output_folder_1 = os.path.join(output_dir, config_intermediate_dirs["CC_brut"])
    output_folder_2 = os.path.join(output_dir, config_intermediate_dirs["CC_brut_color"])
    output_folder_3 = os.path.join(output_dir, config_intermediate_dirs["CC_fillgap"])
    output_folder_4 = os.path.join(output_dir, config_intermediate_dirs["CC_fillgap_color"])
    output_folder_5 = os.path.join(output_dir, config_intermediate_dirs["CC_crop"])

    # Step 1 : Write raster brut
    raster_brut = step1_create_raster_brut(
        in_points=in_points,
        output_dir=output_folder_1,
        output_filename=input_las_name_without_extension,
        res=pixel_size,
        i=1,
        output_extension=extension,
        raster_driver=raster_driver,
    )

    # Step 2 : Color brut
    step3_color_raster(
        in_raster=raster_brut,
        output_dir=output_folder_2,
        tilename=input_las_name_without_extension,
        output_extension=extension,
        verbose="raster_color",
        i=2,
        LUT=LUT,
    )

    # Step 3 :  Fill gaps
    fillgap_raster = step2_create_raster_fillgap(
        in_raster=raster_brut,
        output_dir=output_folder_3,
        output_filename=input_las_name_without_extension,
        output_extension=extension,
        i=3,
        raster_driver=raster_driver,
    )

    # Step 4 : Color fill gaps
    color_fillgap_raster = step3_color_raster(
        in_raster=fillgap_raster,
        output_dir=output_folder_4,
        tilename=input_las_name_without_extension,
        output_extension=extension,
        verbose="raster_fillgap_color",
        i=4,
        LUT=LUT,
    )
    # Step 5: Crop
    os.makedirs(output_folder_5, exist_ok=True)
    output_clip_raster = os.path.join(output_folder_5, f"{input_las_name_without_extension}_raster{extension}")
    clip_raster.clip_raster(input_raster=color_fillgap_raster, output_raster=output_clip_raster, bounds=output_bounds,
                            raster_driver=raster_driver)

    return output_clip_raster



@hydra.main(config_path="../configs/", config_name="config_ctview.yaml", version_base="1.2")
def main(config: DictConfig):
    log.basicConfig(level=log.INFO, format="%(message)s")
    initial_las_file = os.path.join(config.io.input_dir, config.io.input_filename)
    las_bounds = utils_pdal.get_bounds_from_las(initial_las_file)
    os.makedirs(config.io.output_dir, exist_ok=True)
    create_map_class(
        input_las=initial_las_file,
        output_dir=config.io.output_dir,
        config_intermediate_dirs=config.class_map.intermediate_dirs,
        pixel_size=config.class_map.pixel_size,
        extension=config.io.extension,
        LUT=os.path.join(config.io.lut_folder, config.class_map.lut_filename),
        output_bounds=las_bounds,
        raster_driver=config.io.raster_driver,
    )
    log.info("END.")


if __name__ == "__main__":
    main()
