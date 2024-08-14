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

import ctview.map_class.raster_generation as map_class
import ctview.map_density as map_density
from ctview import utils_raster


@hydra.main(config_path="../configs/", config_name="config_metadata.yaml", version_base="1.2")
def main(config: DictConfig):
    log.basicConfig(level=log.INFO, format="%(message)s")

    in_las = config.io.input_filename
    in_dir = config.io.input_dir
    out_dir = config.io.output_dir
    epsg = config.io.spatial_reference
    tile_coord_scale = config.io.tile_geometry.tile_coord_scale
    tile_width = config.io.tile_geometry.tile_width
    buffer_size = config.buffer.size

    # Verify args are ok
    if in_las is None or in_dir is None:
        raise RuntimeError(
            "In input you have to give a las and a directory. For more info run the same command by adding --help"
        )
    if out_dir is None:
        raise RuntimeError("No output directory. For more info run the same command by adding --help")
    # Create folders
    os.makedirs(out_dir, exist_ok=True)
    out_dir_density = Path(out_dir) / "density"
    out_dir_class = Path(out_dir) / "class"
    out_dir_class_pretty = Path(out_dir) / "class_pretty"
    os.makedirs(out_dir_density, exist_ok=True)
    os.makedirs(out_dir_class, exist_ok=True)
    os.makedirs(out_dir_class_pretty, exist_ok=True)

    input_las = os.path.join(in_dir, in_las)
    tilename, _ = os.path.splitext(in_las)

    with tempfile.TemporaryDirectory(prefix="tmp_buffer", dir="tmp") as tmpdir:
        if config.buffer.output_subdir:
            las_with_buffer = Path(out_dir) / config.buffer.output_subdir / in_las
        else:
            las_with_buffer = Path(tmpdir) / in_las
        las_with_buffer.parent.mkdir(parents=True, exist_ok=True)

        # Buffer
        create_las_with_buffer(
            input_dir=in_dir,
            tile_filename=input_las,
            output_filename=str(las_with_buffer),
            buffer_width=buffer_size,
            spatial_ref=f"EPSG:{epsg}",
            tile_width=tile_width,
            tile_coord_scale=tile_coord_scale,
        )
        filename_density = f"{tilename}_density.tif"
        output_tif_density = os.path.join(out_dir_density, filename_density)

        # Read las
        las = laspy.read(las_with_buffer)
        points_np = np.vstack((las.x, las.y, las.z)).transpose()
        classifs = np.copy(las.classification)

        density_raster_origin = utils_raster.compute_raster_origin(
            input_points=points_np,
            tile_width=tile_width,
            pixel_size=config.density.pixel_size,
            buffer_size=buffer_size,
        )

        # Density
        map_density.generate_raster_of_density(
            input_points=points_np,
            input_classifs=classifs,
            output_tif=output_tif_density,
            epsg=epsg,
            raster_origin=density_raster_origin,
            classes_by_layer=config.density.keep_classes,
            tile_width=tile_width,
            pixel_size=config.density.pixel_size,
            raster_driver=config.io.raster_driver,
        )

        # Class map
        class_map_raster_origin = utils_raster.compute_raster_origin(
            input_points=points_np,
            tile_width=tile_width,
            pixel_size=config.class_map.pixel_size,
            buffer_size=buffer_size,
        )

        class_raster_path = map_class.generate_class_raster(
            input_points=points_np,
            input_classifs=classifs,
            tilename=tilename,
            output_dir=out_dir_class,
            config_class=config.class_map,
            config_io=config.io,
            config_geometry=config.io.tile_geometry,
            raster_origin=class_map_raster_origin,
        )

        map_class.generate_pretty_class_raster_from_single_band_raster(
            input_raster=class_raster_path,
            input_las=las_with_buffer,
            tilename=tilename,
            output_dir=out_dir_class_pretty,
            config_class=config.class_map,
            config_io=config.io,
        )


if __name__ == "__main__":
    gdal.UseExceptions()
    main()
