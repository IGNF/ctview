# Autor : ELucon

import argparse
import logging as log
import os
from numbers import Real
from typing import Optional

import numpy as np
from hydra import compose, initialize
from omegaconf import DictConfig
from osgeo_utils import gdal_calc, gdal_fillnodata

import ctview.clip_raster as clip_raster
import ctview.utils_gdal as utils_gdal
import ctview.utils_pdal as utils_pdal
from ctview.utils_folder import dico_folder_template


def fill_no_data(
    src_raster: Optional[str] = None,
    dst_raster: Optional[str] = None,
    max_Search_Distance: Real = 2,
):
    """Fill gap in the data.
    input_raster : raster to fill
    output_raster : raster with no gap
    max_Search_Distance : maximum distance (in pixel) that the algorithm will search out for values to interpolate.
    """
    gdal_fillnodata.gdal_fillnodata(
        src_filename=src_raster,
        band_number=2,
        dst_filename=dst_raster,
        driver_name="GTiff",
        creation_options=None,
        quiet=True,
        mask="default",
        max_distance=max_Search_Distance,
        smoothing_iterations=0,
        options=None,
    )


def step1_create_raster_brut(
    in_points: np.ndarray, output_dir: str, filename: str, res: int, i: int, config: DictConfig
):
    """
    Create raster of class brut.
    Args :
        in_points : points of las file
        output_dir : output directory
        filename : name of las file whithout extension
        res : resolution in meters
        i : index step
    Return :
        Full path of raster of class brut
    """
    raster_brut = os.path.join(output_dir, f"{filename}_raster{config.io.extension}")
    log.info(f"Step {i}/4 : Raster of class brut : {raster_brut}")
    utils_pdal.write_raster_class(input_points=in_points, output_raster=raster_brut, res=res)

    if not os.path.exists(raster_brut):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{raster_brut} not found")

    return raster_brut


def step2_create_raster_fillgap(in_raster: str, output_dir: str, filename, i: int, config: DictConfig):
    """
    Fill gaps on a raster using gdal.
    Args :
        in_raster : raster to fill
        output_dir : output directory
        filename : name of las file whithout extension
        i : index step
    Return :
        Full path of raster filled
    """
    fillgap_raster = os.path.join(output_dir, f"{filename}_raster_fillgap{config.io.extension}")
    log.info(f"Step {i}/4 : Fill gaps : {fillgap_raster}")
    fill_no_data(
        src_raster=in_raster,
        dst_raster=fillgap_raster,
        max_Search_Distance=2,  # modif 10/01/2023
    )

    if not os.path.exists(fillgap_raster):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{fillgap_raster} not found")

    return fillgap_raster


def step3_color_raster(in_raster: str, output_dir: str, filename: str, verbose: str, i: int, config: DictConfig):
    """
    Color a raster using method gdal DEMProcessing with a specific LUT.
    Args :
        in_raster : raster to color
        output_dir : output directory
        filename : name of las file whithout extension
        verbose : suffix for the output filename
        i : index step
    Return :
        Full path of raster colored
    """
    raster_colored = os.path.join(output_dir, f"{filename}_{verbose}{config.io.extension}")
    log.info(f"Step {i}/4 : {verbose} : {raster_colored}")

    utils_gdal.color_raster_with_LUT(
        input_raster=in_raster, output_raster=raster_colored, LUT=os.path.join("LUT", "LUT_CLASS.txt")
    )

    if not os.path.exists(raster_colored):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{raster_colored} not found")

    return raster_colored


def create_map_class(input_las: str, output_dir: str, dico_fld: dict, config: DictConfig):
    """
    Create a raster of class with the fill aps method of gdal and a colorisation.
    Args :
        input_las : las file
        output_dir : output directory
    Return :
        Full path of raster filled and colorised
    """
    log.basicConfig(level=log.INFO, format="%(message)s")

    # File names
    input_las_name = os.path.basename(input_las)
    input_las_name_without_extension = os.path.splitext(input_las_name)[0]  # Read las
    in_points = utils_pdal.read_las_file(input_las)

    log.info(f"\nMAP OF CLASS : file : {input_las_name}")

    # Output_folder_names
    output_folder_1 = os.path.join(output_dir, dico_fld["folder_CC_brut"])
    output_folder_2 = os.path.join(output_dir, dico_fld["folder_CC_brut_color"])
    output_folder_3 = os.path.join(output_dir, dico_fld["folder_CC_fillgap"])
    output_folder_4 = os.path.join(output_dir, dico_fld["folder_CC_fillgap_color"])

    # Step 1 : Write raster brut
    raster_brut = step1_create_raster_brut(
        in_points,
        output_folder_1,
        input_las_name_without_extension,
        config.tile_geometry.pixel_size,
        i=1,
        config=config,
    )

    # Step 2 : Color brut
    step3_color_raster(
        in_raster=raster_brut,
        output_dir=output_folder_2,
        filename=input_las_name_without_extension,
        verbose="raster_color",
        i=2,
        config=config,
    )

    # Step 3 :  Fill gaps
    fillgap_raster = step2_create_raster_fillgap(
        raster_brut, output_folder_3, input_las_name_without_extension, i=3, config=config
    )

    # Step 4 : Color fill gaps
    color_fillgap_raster = step3_color_raster(
        in_raster=fillgap_raster,
        output_dir=output_folder_4,
        filename=input_las_name_without_extension,
        verbose="raster_fillgap_color",
        i=4,
        config=config,
    )

    return color_fillgap_raster


def multiply_DSM_class(
    input_DSM: str,
    input_raster_class: str,
    filename: str,
    output_dir: str,
    bounds: tuple,
    config: DictConfig,
):
    """
    Fusion of 2 rasters (DSM and raster of class filled and colored) with a given formula.
    Args :
        input_DSM : DSM
        input_raster_class : raster of class filled and colored
        filename : name of las file whithout path
        output_dir : output directory
        bounds : bounds of las file ([minx,maxx],[miny, maxy])
        dico_fld : dictionnary of subfolders
    """
    # Crop rasters
    log.info("Crop rasters")
    input_DSM_crop = f"{os.path.splitext(input_DSM)[0]}_crop{config.io.extension}"
    clip_raster.clip_raster(input_raster=input_DSM, output_raster=input_DSM_crop, bounds=bounds)

    input_raster_class_crop = f"{os.path.splitext(input_raster_class)[0]}_crop{config.io.extension}"
    clip_raster.clip_raster(input_raster=input_raster_class, output_raster=input_raster_class_crop, bounds=bounds)

    log.info("Multiplication with DSM")
    out_raster = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_fusion_DSM_class{config.io.extension}")
    # Mutiply
    gdal_calc.Calc(
        A=input_raster_class_crop,
        B=input_DSM_crop,
        calc="254*((A*(0.5*(B/255)+0.25))>254)+(A*(0.5*(B/255)+0.25))*((A*(0.5*(B/255)+0.25))<=254)",
        outfile=out_raster,
        allBands="A",
        overwrite=True,
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-las", "--input_las")
    parser.add_argument("-o", "--output_dir")

    return parser.parse_args()


if __name__ == "__main__":
    # Get las file, output directory and interpolation method
    args = parse_args()
    in_las = args.input_las
    out_dir = args.output_dir

    # Create folders
    dico_test = dico_folder_template
    os.makedirs(os.path.join(out_dir, dico_test["folder_CC_brut"]), exist_ok=True)
    os.makedirs(os.path.join(out_dir, dico_test["folder_CC_fillgap"]), exist_ok=True)
    os.makedirs(os.path.join(out_dir, dico_test["folder_CC_brut_color"]), exist_ok=True)
    os.makedirs(os.path.join(out_dir, dico_test["folder_CC_fillgap_color"]), exist_ok=True)
    os.makedirs(os.path.join(out_dir, dico_test["folder_CC_fusion"]), exist_ok=True)

    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
        )
    create_map_class(in_las, out_dir, dico_fld=dico_test, config=cfg.mnx_dsm)
