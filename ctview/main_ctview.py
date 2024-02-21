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
    map_density.create_density_raster_with_color_and_hillshade(
        str(las_with_buffer), tilename, config.density, config.io, config.buffer.size
    )

    # DTM hillshade color
    log.info("\nStep 3: Generate DTM")
    # prepare outputs
    raster_dtm_dxm_raw = os.path.join(
        out_dir,
        config.dtm.intermediate_dirs.dxm_raw,
        f"{tilename}_interp{config.io.extension}",
    )
    raster_dtm_dxm_hillshade = os.path.join(
        out_dir,
        config.dtm.intermediate_dirs.dxm_hillshade,
        f"{tilename}_hillshade{config.io.extension}",
    )

    dir_dtm_colored = os.path.join(out_dir, config.dtm.output_subdir)
    dir_dtm_lut = os.path.join(out_dir, config.dtm.color.folder_LUT)

    log.info("\nStep 3.1: Generate DTM with hillshade")
    map_DXM.create_colored_dxm_with_hillshade(
        input_file=str(las_with_buffer),
        output_dir=dir_dtm_colored,
        output_dxm_raw=raster_dtm_dxm_raw,
        output_dxm_hillshade=raster_dtm_dxm_hillshade,
        pixel_size=config.dtm.pixel_size,
        keep_classes=config.dtm.keep_classes,
        dxm_interpolation=config.dtm.interpolation,
        color_cycles=config.dtm.color.cycles_DTM_colored,
        output_dir_LUT=dir_dtm_lut,
        config_io=config.io,
    )

    # Map class color
    log.info("\nStep 4: Generate Classification map")
    log.info("\nStep 4.1: Generate MNs for hillshade")

    log.info("\nStep 4.1: Generate colored class map with post-processing")
    raster_class_fgc = map_class.create_map_class(
        input_las=str(las_with_buffer),
        output_dir=out_dir,
        pixel_size=config.class_map.pixel_size,
        extension=config.io.extension,
        config_intermediate_dirs=config.class_map.intermediate_dirs,
        LUT=os.path.join(config.io.lut_folder, config.class_map.lut_filename),
        output_bounds=bounds_las,
        raster_driver=config.io.raster_driver,
    )

    # prepare outputs
    raster_class_map_dxm_raw = os.path.join(
        out_dir,
        config.class_map.intermediate_dirs.dxm_raw,
        f"{tilename}_interp{config.io.extension}",
    )
    raster_class_map_dxm_hillshade = os.path.join(
        out_dir,
        config.class_map.intermediate_dirs.dxm_hillshade,
        f"{tilename}_hillshade{config.io.extension}",
    )
    output_dir_map_class_color = os.path.join(out_dir, config.class_map.output_subdir)
    os.makedirs(output_dir_map_class_color, exist_ok=True)

    raster_class_map = os.path.join(
        out_dir,
        config.class_map.output_subdir,
        f"{tilename}_fusion_DSM_class{config.io.extension}",
    )
    os.makedirs(os.path.dirname(raster_class_map), exist_ok=True)

    map_DXM.add_dxm_hillshade_to_raster(
        input_raster=raster_class_fgc,
        input_pointcloud=str(las_with_buffer),
        output_raster=raster_class_map,
        pixel_size=config.class_map.pixel_size,
        keep_classes=config.class_map.keep_classes,
        dxm_interpolation=config.class_map.dxm_interpolation,
        output_dxm_raw=raster_class_map_dxm_raw,
        output_dxm_hillshade=raster_class_map_dxm_hillshade,
        hillshade_calc=config.class_map.hillshade_calc,
        config_io=config.io,
    )


if __name__ == "__main__":
    main()
