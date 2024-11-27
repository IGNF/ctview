import logging as log
import os
import tempfile
from pathlib import Path

import hydra
import laspy
import numpy as np
from omegaconf import DictConfig
from osgeo import gdal
from pdaltools.las_add_buffer import create_las_with_buffer
from pdaltools.las_info import get_tile_origin_using_header_info

import ctview.map_class.raster_generation as map_class
import ctview.map_density as map_density
from ctview import utils_raster


def main_ctview(config: DictConfig):
    log.basicConfig(level=log.INFO, format="%(message)s")

    initial_las_filename = config.io.input_filename
    tilename = os.path.splitext(initial_las_filename)[0]

    in_dir = config.io.input_dir
    out_dir = config.io.output_dir

    # Check input/output files and folders
    if initial_las_filename is None or in_dir is None or out_dir is None:
        raise RuntimeError(
            """In input you have to give a las, an input directory and an output directory.
            For more info run the same command by adding --help"""
        )

    os.makedirs(out_dir, exist_ok=True)

    tilename = os.path.splitext(initial_las_filename)[0]
    initial_las_file = os.path.join(in_dir, initial_las_filename)

    with (
        tempfile.TemporaryDirectory(prefix="tmp_buffer", dir="tmp") as tmpdir_buffer,
        tempfile.TemporaryDirectory(prefix="tmp_class_raw", dir="tmp") as tmpdir_class,
    ):
        # Get pointcloud origin from the las file metadata
        tile_origin = get_tile_origin_using_header_info(
            initial_las_file, tile_width=config.io.tile_geometry.tile_width
        )

        # Buffer
        log.info(f"\nStep 1: Create buffered las file with buffer = {config.buffer.size}")
        if config.buffer.output_subdir:
            las_with_buffer = Path(out_dir) / config.buffer.output_subdir / initial_las_filename
        else:
            las_with_buffer = Path(tmpdir_buffer) / initial_las_filename
        las_with_buffer.parent.mkdir(parents=True, exist_ok=True)

        epsg = config.io.spatial_reference
        create_las_with_buffer(
            input_dir=str(in_dir),
            tile_filename=initial_las_file,
            output_filename=str(las_with_buffer),
            buffer_width=config.buffer.size,
            spatial_ref=f"EPSG:{epsg}" if str(epsg).isdigit() else epsg,
            tile_width=config.io.tile_geometry.tile_width,
            tile_coord_scale=config.io.tile_geometry.tile_coord_scale,
        )

        # Read las
        las = laspy.read(las_with_buffer)
        points_np = np.vstack((las.x, las.y, las.z)).transpose()
        classifs = np.copy(las.classification)

        if config.density.output_subdir:
            # Map density
            log.info("\nStep 2: Generate a density map")
            map_density.create_density_raster_from_config(
                str(las_with_buffer), tile_origin, tilename, config.density, config.io
            )

        else:
            log.info("\nStep 2: Skip density map")

        if config.class_map.output_class_subdir or config.class_map.output_class_pretty_subdir:
            # Map classes
            log.info("\nStep 3: Generate a classification map")

            if config.class_map.output_class_subdir:
                output_class_dir = Path(out_dir) / config.class_map.output_class_subdir
            else:
                output_class_dir = Path(tmpdir_class)
            output_class_dir.mkdir(parents=True, exist_ok=True)

            class_map_raster_origin = utils_raster.compute_raster_origin(
                tile_origin,
                pixel_size=config.class_map.pixel_size,
            )

            class_raster_path = map_class.generate_class_raster(
                input_points=points_np,
                input_classifs=classifs,
                tilename=tilename,
                output_dir=output_class_dir,
                config_class=config.class_map,
                config_io=config.io,
                config_geometry=config.io.tile_geometry,
                raster_origin=class_map_raster_origin,
            )

            if config.class_map.output_class_pretty_subdir:
                output_class_pretty_subdir = Path(out_dir) / config.class_map.output_class_pretty_subdir
                os.makedirs(output_class_pretty_subdir, exist_ok=True)
                map_class.generate_pretty_class_raster_from_single_band_raster(
                    input_raster=class_raster_path,
                    input_las=las_with_buffer,
                    tilename=tilename,
                    output_dir=output_class_pretty_subdir,
                    config_class=config.class_map,
                    config_io=config.io,
                )

        else:
            log.info("\nStep 3: Skip classification map")


@hydra.main(config_path="../configs/", config_name="config_control.yaml", version_base="1.2")
def main(config: DictConfig):
    main_ctview(config)


if __name__ == "__main__":
    gdal.UseExceptions()
    main()
