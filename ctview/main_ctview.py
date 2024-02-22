import logging as log
import os
from pathlib import Path

import hydra
from omegaconf import DictConfig
from pdaltools.las_add_buffer import create_las_with_buffer

import ctview.map_class as map_class
import ctview.map_density as map_density
import ctview.map_DXM as map_DXM
import ctview.utils_pdal as utils_pdal


@hydra.main(config_path="../configs/", config_name="config_ctview.yaml", version_base="1.2")
def main(config: DictConfig):
    log.basicConfig(level=log.INFO, format="%(message)s")

    initial_las_filename = config.io.input_filename
    tilename = os.path.splitext(initial_las_filename)[0]

    # Check input/output files and folders
    in_dir = config.io.input_dir
    out_dir = config.io.output_dir

    if initial_las_filename is None or in_dir is None or out_dir is None:
        raise RuntimeError(
            """In input you have to give a las, an input directory and an output directory.
            For more info run the same command by adding --help"""
        )

    os.makedirs(out_dir, exist_ok=True)

    # ## ACTIVATE IF NECESSARY
    # log.warning("#########")
    # log.warning("ATTENTION : modification LAS/LAZ file with function utils_tools.repare_file")
    # log.warning("#########")
    # utils_tools.repare_files(las_liste, in_dir)
    # time.sleep(2)
    tilename = os.path.splitext(initial_las_filename)[0]
    initial_las_file = os.path.join(in_dir, initial_las_filename)
    las_with_buffer = Path(out_dir) / config.buffer.output_subdir / initial_las_filename
    las_with_buffer.parent.mkdir(parents=True, exist_ok=True)
    bounds_las = utils_pdal.get_bounds_from_las(initial_las_file)  # get boundaries

    # BUFFER
    log.info(f"\nStep 1: Create buffered las file with buffer = {config.buffer.size}")
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

    # DENSITY (DTM brut + density)
    log.info("\nStep 2: Generate a density map with hillshade and color")
    map_density.create_density_raster_with_color_and_hillshade(
        str(las_with_buffer), tilename, config.density, config.io, config.buffer.size
    )

    # DTM hillshade color
    log.info("\nStep 3: Generate dtm(s) with hillshade and color")
    map_DXM.create_colored_dxm_with_hillshade(
        input_las=str(las_with_buffer),
        tilename=tilename,
        config_dtm=config.dtm,
        config_io=config.io,
    )

    # Map class color
    log.info("\nStep 4: Generate a classification map with hillshade and color")
    map_class.create_map_class_raster_with_postprocessing_color_and_hillshade(
        input_las=str(las_with_buffer),
        tilename=tilename,
        config_class=config.class_map,
        config_io=config.io,
        output_bounds=bounds_las,
    )


if __name__ == "__main__":
    main()
