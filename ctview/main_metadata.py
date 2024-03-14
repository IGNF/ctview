import logging as log
import os
import tempfile
from pathlib import Path

import hydra
import laspy
import numpy as np
from omegaconf import DictConfig
from pdaltools.las_add_buffer import create_las_with_buffer

import ctview.map_density as map_density
import ctview.map_class as map_class


@hydra.main(config_path="../configs/", config_name="config_metadata.yaml", version_base="1.2")
def main(config: DictConfig):
    log.basicConfig(level=log.INFO, format="%(message)s")

    in_las = config.io.input_filename
    in_dir = config.io.input_dir
    out_dir = config.io.output_dir
    tile_coord_scale = config.tile_geometry.tile_coord_scale
    tile_size = config.tile_geometry.tile_size
    pixel_size = config.density.pixel_size
    buffer_size = config.buffer.buffer_size
    epsg = config.io.projection_epsg

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
    os.makedirs(out_dir_density, exist_ok=True)
    os.makedirs(out_dir_class, exist_ok=True)

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
            tile_width=tile_size,
            tile_coord_scale=tile_coord_scale,
        )
        filename_density = f"{tilename}_density.tif"
        output_tif_density = os.path.join(out_dir_density, filename_density)
        filename_class_raw = f"{tilename}_class_raw.tif"
        output_tif_class_raw = os.path.join(out_dir_class, filename_class_raw)

        # Read las
        las = laspy.read(las_with_buffer)
        points_np = np.vstack((las.x, las.y, las.z)).transpose()
        classifs = np.copy(las.classification)

        # Density
        map_density.generate_raster_of_density(
            input_points=points_np,
            input_classifs=classifs,
            output_tif=output_tif_density,
            epsg=epsg,
            classes_by_layer=config.density.keep_classes,
            tile_size=tile_size,
            pixel_size=pixel_size,
            buffer_size=buffer_size,
            raster_driver=config.io.raster_driver,
        )

        # Class map
        map_class.generate_class_raster_raw(
            input_points=points_np,
            input_classifs=classifs,
            output_tif=output_tif_class_raw,
            epsg=epsg,
            classes_by_layer=config.class_map.keep_classes,
            tile_size=tile_size,
            pixel_size=pixel_size,
            buffer_size=buffer_size,
            raster_driver=config.io.raster_driver,
        )


if __name__ == "__main__":
    main()
