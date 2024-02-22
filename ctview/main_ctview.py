import logging as log
import os
from pathlib import Path

import hydra
import laspy
import numpy as np
from omegaconf import DictConfig
from pdaltools.las_add_buffer import create_las_with_buffer

import ctview.add_color as add_color
import ctview.map_class as map_class
import ctview.map_density as map_density
import ctview.map_DXM as map_DXM
import ctview.utils_gdal as utils_gdal
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
    las_with_buffer = Path(out_dir) / config.buffer.output_dir / initial_las_filename
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
        tile_width=config.tile_geometry.tile_width,
        tile_coord_scale=config.tile_geometry.tile_coord_scale,
    )

    # DENSITY (DTM brut + density)
    log.info("\nStep 2: Create density maps")
    log.info("\nStep 2.1: Create dtm map for density shading")

    # prepare outputs
    raster_density_dxm_raw = os.path.join(
        out_dir,
        config.density.intermediate_dirs.dxm_raw,
        f"{tilename}_interp{config.io.extension}",
    )
    raster_density_dxm_hillshade = os.path.join(
        out_dir,
        config.density.intermediate_dirs.dxm_hillshade,
        f"{tilename}_hillshade{config.io.extension}",
    )

    # Filename and config.tile_geometry are used to generate rasters with the expected geometry
    map_DXM.create_dxm_with_hillshade_one_las(
        input_file=str(las_with_buffer),
        output_dxm_raw=raster_density_dxm_raw,
        output_dxm_hillshade=raster_density_dxm_hillshade,
        pixel_size=config.density.pixel_size,
        keep_classes=config.density.keep_classes,
        dxm_interpolation=config.density.dxm_interpolation,
        config=config,
        type_raster="dtm_dens",
    )

    log.info("\nStep 2.2: Create density map\n")
    raster_dens_values = os.path.join(
        out_dir,
        config.density.intermediate_dirs.density_values,
        f"{tilename}_DENS{config.io.extension}",
    )
    os.makedirs(os.path.dirname(raster_dens_values), exist_ok=True)
    raster_dens_color = os.path.join(
        out_dir,
        config.density.intermediate_dirs.density_color,
        f"{tilename}_DENS_COLOR{config.io.extension}",
    )
    os.makedirs(os.path.dirname(raster_dens_color), exist_ok=True)
    raster_dens = os.path.join(
        out_dir,
        config.density.output_dir,
        f"{tilename}_DENS{config.io.extension}",
    )
    os.makedirs(os.path.dirname(raster_dens), exist_ok=True)

    # DENSITY
    las = laspy.read(str(las_with_buffer))
    points_np = np.vstack((las.x, las.y, las.z)).transpose()
    classifs = np.copy(las.classification)

    map_density.generate_raster_of_density(
        input_points=points_np,
        input_classifs=classifs,
        output_tif=raster_dens_values,
        epsg=config.io.spatial_reference,
        classes_by_layer=[config.density.keep_classes],
        tile_size=config.tile_geometry.tile_width,
        pixel_size=config.density.pixel_size,
        buffer_size=config.buffer.size,
        raster_driver=config.io.raster_driver,
    )

    log.info("\nStep 2.3: Colorize density map\n")
    utils_gdal.color_raster_with_LUT(
        input_raster=raster_dens_values,
        output_raster=raster_dens_color,
        LUT=os.path.join(config.io.lut_folder, config.density.lut_filename),
    )

    log.info("\nStep 2.4: Multiply with DTM for hillshade")
    map_density.multiply_DTM_density(
        input_DTM=raster_density_dxm_hillshade,
        input_dens_raster=raster_dens_color,
        output_raster=raster_dens,
        no_data=config.tile_geometry.no_data_value,
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

    log.info("\nStep 3.1: Generate DTM with hillshade")
    map_DXM.create_dxm_with_hillshade_one_las(
        input_file=str(las_with_buffer),
        output_dxm_raw=raster_dtm_dxm_raw,
        output_dxm_hillshade=raster_dtm_dxm_hillshade,
        pixel_size=config.dtm.pixel_size,
        keep_classes=config.dtm.keep_classes,
        dxm_interpolation=config.dtm.interpolation,
        config=config,
        type_raster="dtm",
    )

    log.info("\nStep 3.2: Colorize DTM")
    add_color.color_raster_dtm_hillshade_with_LUT(
        input_initial_basename=initial_las_filename,
        input_raster=raster_dtm_dxm_hillshade,
        output_dir=os.path.join(out_dir, config.dtm.output_dir),
        list_c=config.dtm.color.cycles_DTM_colored,
        output_dir_LUT=os.path.join(out_dir, config.dtm.color.folder_LUT),
    )

    # Map class color
    log.info("\nStep 4: Generate Classification map")
    log.info("\nStep 4.1: Generate MNs for hillshade")

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
    output_dir_map_class_color = os.path.join(out_dir, config.class_map.output_dir)
    os.makedirs(output_dir_map_class_color, exist_ok=True)

    map_DXM.create_dxm_with_hillshade_one_las(
        input_file=str(las_with_buffer),
        output_dxm_raw=raster_class_map_dxm_raw,
        output_dxm_hillshade=raster_class_map_dxm_hillshade,
        pixel_size=config.class_map.pixel_size,
        keep_classes=config.class_map.keep_classes,
        dxm_interpolation=config.class_map.dxm_interpolation,
        config=config,
        type_raster="dsm",
    )

    log.info("\nStep 4.1: Generate colored class map with post-processing")
    raster_class_fgc = map_class.create_map_class(
        input_las=str(las_with_buffer),
        output_dir=out_dir,
        pixel_size=config.class_map.pixel_size,
        extension=config.io.extension,
        config_intermediate_dirs=config.class_map.intermediate_dirs,
        LUT=os.path.join(config.io.lut_folder, config.class_map.lut_filename),
        raster_driver=config.io.raster_driver,
    )

    log.info("\nStep 4.2: Multiply with DSM for hillshade")
    map_class.multiply_DSM_class(
        input_DSM=raster_class_map_dxm_hillshade,
        input_raster_class=raster_class_fgc,
        output_dir=output_dir_map_class_color,
        output_filename=initial_las_filename,
        output_extension=config.io.extension,
        bounds=bounds_las,
        raster_driver=config.io.raster_driver,
    )


if __name__ == "__main__":
    main()
