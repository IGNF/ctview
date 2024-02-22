import logging as log
import os
from typing import List

import ctview.gen_LUT_X_cycle as gen_LUT_X_cycle
import ctview.utils_gdal as utils_gdal


def color_raster_dtm_hillshade_with_LUT(
    input_initial_basename: str, input_raster: str, output_dir: str, list_c: List[int], output_dir_LUT: str
):
    """Color a raster according to:
    - the color palette defined in a LUT file
    - numbers of cycles: one output raster will be create for each of the numbers in the list


    Args:
        input_initial_basename (str): basename of the initial LAS file (use to name the output raster)
        input_raster (str): path to the raster to color
        output_dir (str): output directory
        list_c (List[int]): the number of cycles that determines how th use the LUT.
        One colored raster will be created for each of the numbers of cycles in the list
        output_dir_LUT (str): output path for the LUT corresponding to each output raster
    """
    log.info("Build DTM hillshade color")

    cpt = 1

    for cycle in list_c:
        log.info(f"{cpt}/{len(list_c)}...")
        folder_DXM_color = f"{cycle}cycle{'s' if cycle > 1 else ''}"
        output_dir_raster = os.path.join(output_dir, folder_DXM_color)
        os.makedirs(output_dir_raster, exist_ok=True)

        color_DTM_with_cycles(
            las_input_file=input_initial_basename,
            output_dir_raster=output_dir_raster,
            output_dir_LUT=output_dir_LUT,
            raster_DTM_file=input_raster,
            nb_cycle=cycle,
        )

        cpt += 1

    log.info("End DTM.\n")


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
    os.makedirs(output_dir_LUT, exist_ok=True)
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
