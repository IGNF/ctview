# Autor : ELucon


import argparse
import logging as log
import os
import shutil
from typing import Tuple

import numpy as np
import pdal
import rasterio
from hydra import compose, initialize
from omegaconf import DictConfig
from osgeo_utils import gdal_calc

import ctview.clip_raster as clip_raster
import ctview.utils_gdal as utils_gdal
import ctview.utils_pdal as utils_pdal
from ctview.utils_folder import dico_folder_template
from ctview.utils_tools import get_pointcloud_origin

FOLDER_DENS_VALUE = dico_folder_template["folder_density_value"]
FOLDER_DENS_COLOR = dico_folder_template["folder_density_color"]
CLASSIF_GROUND = 2


def generate_raster_of_density_2(
    input_points: np.array,
    input_classifs: np.array,
    output_tif: str,
    epsg: int,
    classes_by_layer: list = [[]],
    tile_size: int = 1000,
    pixel_size: float = 1,
    buffer_size: float = 0,
    no_data_value: int = -9999,
):
    pcd_origin_x, pcd_origin_y = get_pointcloud_origin(input_points, tile_size, buffer_size)

    raster_origin = (pcd_origin_x - pixel_size / 2, pcd_origin_y + pixel_size / 2)

    rasters = []
    for classes in classes_by_layer:
        if classes:
            filtered_points = input_points[np.isin(input_classifs, classes), :]
        else:
            filtered_points = input_points

        rasters.append(compute_density(filtered_points, raster_origin, tile_size, pixel_size))

    rasters = np.array(rasters)
    with rasterio.Env():
        with rasterio.open(
            output_tif,
            "w",
            driver="GTiff",
            height=rasters.shape[1],
            width=rasters.shape[2],
            count=rasters.shape[0],
            dtype=rasterio.float32,
            crs=f"EPSG:{epsg}",
            transform=rasterio.transform.from_origin(raster_origin[0], raster_origin[1], pixel_size, pixel_size),
            nodata=no_data_value,
        ) as out_file:
            out_file.write(rasters.astype(rasterio.float32))

    log.debug(f"Saved to {output_tif}")


def compute_density(points: np.array, origin: Tuple[int, int], tile_size: int, pixel_size: float):
    # Compute number of points per bin
    bins_x = np.arange(origin[0], origin[0] + tile_size + pixel_size, pixel_size)
    bins_y = np.arange(origin[1] - tile_size, origin[1] + pixel_size, pixel_size)
    bins, _, _ = np.histogram2d(points[:, 1], points[:, 0], bins=[bins_y, bins_x])
    density = bins / (pixel_size**2)
    density = np.flipud(density)

    return density


def generate_raster_of_density(input_las: str, output_dir: str, config: DictConfig, bounds: str = None):
    """
    Build a raster of density colored.
    Args :
        input_las : las file
        output_dir : output directory
        config : config
        bounds : bounds
    Return :
        path of the raster of density colored
    """
    # Get filename without extension
    input_filename = os.path.basename(input_las)

    # Build raster count point
    raster_name_count = os.path.join(
        output_dir, FOLDER_DENS_VALUE, f"{os.path.splitext(input_filename)[0]}_COUNT{config.io.extension}"
    )
    raster_name_dens = os.path.join(
        output_dir, FOLDER_DENS_VALUE, f"{os.path.splitext(input_filename)[0]}_DENS{config.io.extension}"
    )

    log.info(f"\nRaster of density at resolution {config.tile_geometry.pixel_size} meter(s) : {input_filename}\n")

    # Raster of density : count points in resolution*resolution m² (Default=25 m²)
    log.info(f"Raster count points at resolution {config.tile_geometry.pixel_size} meter(s)")
    success = method_writer_gdal(input_las=input_las, output_file=raster_name_count, config=config, bounds=bounds)

    if success:
        # Overwrite and change unity of count from "per 25 m²" to "per m²"
        change_unit(
            input_raster=raster_name_count, output_raster=raster_name_dens, res=config.tile_geometry.pixel_size
        )

        # Color density
        raster_name_dens_color = os.path.join(
            output_dir, FOLDER_DENS_COLOR, f"{os.path.splitext(input_filename)[0]}_DENS_COLOR{config.io.extension}"
        )

        log.info("Colorisation...")
        utils_gdal.color_raster_with_LUT(
            input_raster=raster_name_dens,
            output_raster=raster_name_dens_color,
            LUT=os.path.join("LUT", "LUT_DENSITY.txt"),
        )

        return raster_name_dens_color, success

    else:
        return "_", success


def method_writer_gdal(input_las: str, output_file: str, config: DictConfig, bounds: str = None):
    log.debug("method_writer_gdal")
    log.debug(f"raster name output count points : {output_file}")
    log.debug(f"bounds is : {bounds}")
    log.debug(f"resolution utilisée : {config.tile_geometry.pixel_size}")
    log.debug(f"radius :{config.tile_geometry.radius}")

    # Check if the las file contains ground points (redmine 2068)
    pts_to_check = utils_pdal.read_las_file(input_las=input_las)
    pts_ground = np.where(pts_to_check["Classification"] == CLASSIF_GROUND, 1, 0)
    nb_pts_ground = np.count_nonzero(pts_ground == 1)

    is_count_ok = True

    if nb_pts_ground > 0:
        pipeline = pdal.Filter.range(limits="Classification[2:2]").pipeline(pts_to_check)

        if bounds is None:
            pipeline |= pdal.Writer.gdal(
                filename=output_file,
                resolution=config.tile_geometry.pixel_size,
                radius=config.tile_geometry.radius,
                output_type="count",
            )
        else:
            log.info(f"Bounds forced (remove 1 pixel at resolution density) :{bounds}")
            pipeline |= pdal.Writer.gdal(
                filename=output_file,
                resolution=config.tile_geometry.pixel_size,
                radius=config.tile_geometry.radius,
                output_type="count",
                bounds=str(bounds),
            )

        pipeline.execute()

        return is_count_ok

    else:
        is_count_ok = False
        return is_count_ok


def change_unit(input_raster: str, output_raster: str, res: int):
    """
    Overwrite and change unity of count from "per res*res m²" to "per m²
    Args :
        raster_name : raster of density with units res*res m²
        res : resolution of the raster
    """
    gdal_calc.Calc(
        f"A/{res*res}",
        outfile=output_raster,
        A=input_raster,
        quiet=True,
    )


def multiply_DTM_density(
    input_DTM: str, input_dens_raster: str, filename: str, output_dir: str, config: DictConfig, bounds: tuple
):
    """
    Fusion of 2 rasters (DTM and raster of density) with a given formula.
    Args :
        input_DTM : DTM
        input_dens_raster : raster of density
        filename : name of las file whithout path
        output_dir : output directory
        bounds : bounds of las file ([minx,maxx],[miny, maxy])
    """
    # Crop rasters
    log.info("Crop rasters")
    input_DTM_crop = f"{os.path.splitext(input_DTM)[0]}_crop{config.io.extension}"
    clip_raster.clip_raster(input_raster=input_DTM, output_raster=input_DTM_crop, bounds=bounds)

    input_dens_raster_crop = f"{os.path.splitext(input_dens_raster)[0]}_crop{config.io.extension}"
    clip_raster.clip_raster(input_raster=input_dens_raster, output_raster=input_dens_raster_crop, bounds=bounds)

    log.info("Multiplication with DTM")
    # Output file
    out_raster = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_DENS{config.io.extension}")
    # Mutiply
    gdal_calc.Calc(
        A=input_DTM_crop,
        B=input_dens_raster_crop,
        calc="((A-1)<0)*B*(A/255)+((A-1)>=0)*B*((A-1)/255)",
        outfile=out_raster,
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-idir", "--input_las")
    parser.add_argument("-odir", "--output_dir")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    input_las = args.input_las
    output_dir = args.output_dir

    # Create directory if not exists
    if os.path.exists(output_dir):
        # Clean folder test if exists
        shutil.rmtree(output_dir)
    else:
        # Create folder test if not exists
        os.makedirs(output_dir)
    os.makedirs(os.path.join(output_dir, FOLDER_DENS_VALUE), exist_ok=True)
    os.makedirs(os.path.join(output_dir, FOLDER_DENS_COLOR), exist_ok=True)

    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
        )

    generate_raster_of_density(input_las=input_las, output_dir=output_dir, config=cfg.mnx_dtm_dens)
