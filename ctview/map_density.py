import logging as log
import os
from typing import Tuple

import numpy as np
import pdal
import rasterio
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


def generate_raster_of_density(
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
            crs=f"EPSG:{epsg}" if str(epsg).isdigit() else epsg,
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
        NoDataValue=config.tile_geometry.no_data_value,
    )
