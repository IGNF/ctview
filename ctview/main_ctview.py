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
from ctview.utils_folder import create_folder, dico_folder_template


@hydra.main(config_path="../configs/", config_name="config_ctview.yaml", version_base="1.2")
def main(config: DictConfig):
    log.basicConfig(level=log.INFO, format="%(message)s")

    initial_las_filename = config.io.input_filename
    in_dir = config.io.input_dir
    out_dir = config.io.output_dir
    list_cycles = config.dtm.color.cycles_DTM_colored

    # Verify args are ok
    if initial_las_filename is None or in_dir is None or out_dir is None:
        raise RuntimeError(
            """In input you have to give a las, an input directory and an output directory.
            For more info run the same command by adding --help"""
        )

    dico_folder_modif = dico_folder_template.copy()

    # Create folder test if not exists
    os.makedirs(out_dir, exist_ok=True)

    # Create folders of dico_folder_modif in out_dir
    create_folder(out_dir, dico_fld=dico_folder_modif)
    output_dir_map_density = os.path.join(out_dir, config.io.output_folder_map_density)
    os.makedirs(output_dir_map_density, exist_ok=True)
    output_dir_map_class_color = os.path.join(out_dir, config.io.output_folder_map_class_color)
    os.makedirs(output_dir_map_class_color, exist_ok=True)

    # ## ACTIVATE IF NECESSARY
    # log.warning("#########")
    # log.warning("ATTENTION : modification LAS/LAZ file with function utils_tools.repare_file")
    # log.warning("#########")
    # utils_tools.repare_files(las_liste, in_dir)
    # time.sleep(2)
    initial_las_file = os.path.join(in_dir, initial_las_filename)
    las_with_buffer = Path(out_dir) / "tmp" / "buffer" / initial_las_filename
    las_with_buffer.parent.mkdir(parents=True, exist_ok=True)
    bounds_las = utils_pdal.get_bounds_from_las(initial_las_file)  # get boundaries

    # Buffer
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
    # Filename and config.tile_geometry are used to generate rasters with the expected geometry
    raster_DTM_dens = map_DXM.create_dxm_with_hillshade_one_las(
        input_file=str(las_with_buffer),
        output_dir=str(out_dir),
        pixel_size=config.density.pixel_size,
        keep_classes=config.density.keep_classes,
        dxm_interpolation=config.density.dxm_interpolation,
        config=config,
        type_raster="dtm_dens",
    )

    log.info("\nStep 2.2: Create density map\n")
    raster_dens = os.path.join(
        out_dir,
        dico_folder_template["folder_density_value"],
        f"{os.path.splitext(initial_las_filename)[0]}_DENS{config.density.extension}",
    )
    raster_dens_color = os.path.join(
        out_dir,
        dico_folder_template["folder_density_color"],
        f"{os.path.splitext(initial_las_filename)[0]}_DENS_COLOR{config.density.extension}",
    )
    # Density
    las = laspy.read(str(las_with_buffer))
    points_np = np.vstack((las.x, las.y, las.z)).transpose()
    classifs = np.copy(las.classification)

    map_density.generate_raster_of_density(
        input_points=points_np,
        input_classifs=classifs,
        output_tif=raster_dens,
        epsg=config.io.spatial_reference,
        classes_by_layer=[config.density.keep_classes],
        tile_size=config.tile_geometry.tile_width,
        pixel_size=config.density.pixel_size,
        buffer_size=config.buffer.size,
    )

    log.info("\nStep 2.3: Colorize density map\n")
    utils_gdal.color_raster_with_LUT(
        input_raster=raster_dens,
        output_raster=raster_dens_color,
        LUT=os.path.join("LUT", "LUT_DENSITY.txt"),
    )

    log.info("\nStep 2.4: Multiply with DTM for hillshade")
    map_density.multiply_DTM_density(
        input_DTM=raster_DTM_dens,
        input_dens_raster=raster_dens_color,
        filename=initial_las_filename,
        output_dir=output_dir_map_density,
        no_data=config.tile_geometry.no_data_value,
        extension=config.density.extension,
    )

    # DTM hillshade color
    log.info("\nStep 3: Generate DTM")
    log.info("\nStep 3.1: Generate DTM with hillshade")
    raster_DTM_hs_1M = map_DXM.create_dxm_with_hillshade_one_las(
        input_file=str(las_with_buffer),
        output_dir=out_dir,
        pixel_size=config.dtm.pixel_size,
        keep_classes=config.dtm.keep_classes,
        dxm_interpolation=config.dtm.interpolation,
        config=config,
        type_raster="dtm",
    )

    log.info("\nStep 3.2: Colorize DTM")
    add_color.color_raster_dtm_hillshade_with_LUT(
        input_initial_basename=initial_las_filename,
        input_raster=raster_DTM_hs_1M,
        output_dir=out_dir,
        list_c=list_cycles,
        dico_fld=dico_folder_modif,
    )

    # Map class color
    log.info("\nStep 4: Generate Classification map")
    log.info("\nStep 4.1: Generate MNs for hillshade")
    raster_DSM_hs = map_DXM.create_dxm_with_hillshade_one_las(
        input_file=str(las_with_buffer),
        output_dir=out_dir,
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
        dico_fld=dico_folder_modif,
        pixel_size=config.class_map.pixel_size,
        extension=config.class_map.extension,
    )

    log.info("\nStep 4.2: Multiply with DSM for hillshade")
    map_class.multiply_DSM_class(
        input_DSM=raster_DSM_hs,
        input_raster_class=raster_class_fgc,
        output_dir=output_dir_map_class_color,
        output_filename=initial_las_filename,
        output_extension=config.class_map.extension,
        bounds=bounds_las,
    )


if __name__ == "__main__":
    main()
