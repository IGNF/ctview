import logging as log
import os
import tempfile
from typing import Dict, List

from osgeo import gdal, gdalconst

import ctview.gen_LUT_X_cycle as gen_LUT_X_cycle


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
    color_raster_with_LUT(
        input_raster=raster_DTM_file,
        output_raster=raster_DTM_color_file,
        LUT=LUT,
    )


def color_raster_with_LUT(input_raster, output_raster, LUT):
    """
    Deprecated (used only for cycle DTM generation, which is not in use anymore)
    Color raster with a LUT
    input_raster : path of raster to colorise
    output_raster : path of raster colorised
    dim : dimension to color
    LUT : dictionnary of color
    """

    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing="color-relief",
        computeEdges=True,
        colorFilename=LUT,
        colorSelection="linear_interpolation",
    )


def color_raster_with_interpolation(input_raster: str, output_raster: str, colormap: List[Dict]):
    """Color raster with a color map. To be used for non-categorical data
    (eg. floating point data such as density values)

    Args:
        input_raster (str): path of raster to colorize
        output_raster (str): path of raster colorized
        colormap (List[Dict]): list of colors description dictionaries.
        Example: [{value: 1, color: [255, 255, 255]},
                  {value: 100, color: [0, 0, 0]}]
        Colors are interpolated between the points in colormap.
    """

    colormap_lines = [f"{row['value']} {row['color'][0]} {row['color'][1]} {row['color'][2]}" for row in colormap]

    with tempfile.NamedTemporaryFile(suffix="colormap.txt", delete=True, dir="./") as colormap_file:
        with open(colormap_file.name, "w") as f:
            f.write("\n".join(colormap_lines))

        gdal.DEMProcessing(
            destName=output_raster,
            srcDS=input_raster,
            processing="color-relief",
            computeEdges=True,
            colorFilename=colormap_file.name,
            colorSelection="linear_interpolation",
        )


def add_colors_as_metadata(tif_file: str, colormap: List[Dict]):
    """Add metadata to the input tif file that correspond to the color map dictionary
    - a Gdal Attribute Table that contains colors and descriptions only for the defined
    categories, and that is readable by QGIS
    - a Color Table that should be readable by any software that can read GeoTiff file,
    that contains colors for all the values up to the maximum value
    (defaults to black for all undefined categories, or generate a color ramp when asked)

    Args:
        tif_file (str): Path to the file to which to add metadata
        colormap (List[Dict]): color map list of dictionaries.
        This list should contain a dictionary for each entry with keys/values like:
         {"value": 3, "description": "Vegetation basse", "color": [0, 255, 0] # RGB}

    """

    # Add colors and descriptions to a Raster Attribute Table to read with QGIS
    # with a pretty legend

    ds = gdal.Open(tif_file)
    band = ds.GetRasterBand(1)
    rat = gdal.RasterAttributeTable()
    rat.CreateColumn("Name", gdalconst.GFT_String, gdalconst.GFU_Name)
    rat.CreateColumn("Value", gdalconst.GFT_Integer, gdalconst.GFU_MinMax)
    rat.CreateColumn("R", gdalconst.GFT_Integer, gdalconst.GFU_Red)
    rat.CreateColumn("G", gdalconst.GFT_Integer, gdalconst.GFU_Green)
    rat.CreateColumn("B", gdalconst.GFT_Integer, gdalconst.GFU_Blue)

    for ii, row in enumerate(colormap):
        rat.SetValueAsString(ii, 0, row["description"])
        rat.SetValueAsInt(ii, 1, row["value"])
        rat.SetValueAsInt(ii, 2, row["color"][0])
        rat.SetValueAsInt(ii, 3, row["color"][1])
        rat.SetValueAsInt(ii, 4, row["color"][2])

    band.SetDefaultRAT(rat)
    # Add colors to a color table to be able to display in orther places + use gdal translate
    colors = gdal.ColorTable()

    for category in colormap:
        colors.SetColorEntry(category["value"], tuple(category["color"]))

    band.SetColorTable(colors)

    # close gdal dataset (cf. https://gis.stackexchange.com/questions/80366/why-close-a-dataset-in-gdal-python)
    band = None
    ds = None


def convert_raster_with_color_metadata_to_rgb(input_raster: str, output_raster: str):
    """Use colormap in the input raster metadata to generate a 3 bands output raster based on
    this colormap.

    Only works for categorized data (dscrete data)

    Args:
        input_raster (str): Path to a single band raster with colormap metadata
        output_raster (str): Path to the output 3 bands (rgb) raster
    """
    ds = gdal.Open(input_raster)
    ds = gdal.Translate(output_raster, ds, rgbExpand="rgb")  # Use colors in metadata
    ds = None  # close file
