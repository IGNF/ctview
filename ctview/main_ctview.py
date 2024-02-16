import logging as log
import os
import laspy
import numpy as np

import hydra
from omegaconf import DictConfig

import ctview.add_color as add_color
import ctview.map_class as map_class
import ctview.map_density as map_density
import ctview.map_DXM as map_DXM
import ctview.utils_pdal as utils_pdal
import ctview.utils_gdal as utils_gdal
from ctview.utils_folder import create_folder, dico_folder_template


@hydra.main(config_path="../configs/", config_name="config_ctview.yaml", version_base="1.2")
def main(config: DictConfig):
    log.basicConfig(level=log.INFO, format="%(message)s")

    initial_las_filename = config.io.input_filename
    in_dir = config.io.input_dir
    out_dir = config.io.output_dir
    list_cycles = config.mnx_dtm.color.cycles_DTM_colored

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
    bounds_las = utils_pdal.get_bounds_from_las(initial_las_file)  # get boundaries

    # DENSITY (DTM brut + density)
    # Step 1/3 : DTM brut
    raster_DTM_dens = map_DXM.create_dxm_with_hillshade_one_las(
        input_file=initial_las_file, output_dir=out_dir, config=config.mnx_dtm_dens, type_raster="dtm_dens"
    )
    # Step 2 : raster of density
    log.info("\nStep 2/3 : raster of density\n")
    raster_dens = os.path.join(
        out_dir,
        dico_folder_template["folder_density_value"],
        f"{os.path.splitext(initial_las_filename)[0]}_DENS{config.mnx_dtm_dens.io.extension}",
    )
    raster_dens_color = os.path.join(
        out_dir,
        dico_folder_template["folder_density_color"],
        f"{os.path.splitext(initial_las_filename)[0]}_DENS_COLOR{config.mnx_dtm_dens.io.extension}",
    )
    # Density
    las = laspy.read(initial_las_file)
    points_np = np.vstack((las.x, las.y, las.z)).transpose()
    classifs = np.copy(las.classification)

    map_density.generate_raster_of_density(
        input_points=points_np,
        input_classifs=classifs,
        output_tif=raster_dens,
        epsg=config.mnx_dtm_dens.io.spatial_reference,
        classes_by_layer=[config.mnx_dtm_dens.filter.keep_classes],
        tile_size=config.mnx_dtm_dens.tile_geometry.tile_width,
        pixel_size=config.mnx_dtm_dens.tile_geometry.pixel_size,
        buffer_size=0,
    )

    log.info("Colorisation...")
    utils_gdal.color_raster_with_LUT(
        input_raster=raster_dens,
        output_raster=raster_dens_color,
        LUT=os.path.join("LUT", "LUT_DENSITY.txt"),
    )

    # Step 3 : multiply density and DTM layers
    log.info("\nStep 3/3 : raster of density\n")

    map_density.multiply_DTM_density(
        input_DTM=raster_DTM_dens,
        input_dens_raster=raster_dens_color,
        filename=initial_las_filename,
        output_dir=output_dir_map_density,
        config=config.mnx_dtm_dens,
        bounds=bounds_las,
    )

    # DTM hillshade color
    # Step 1/2 : DTM hillshade
    raster_DTM_hs_1M = map_DXM.create_dxm_with_hillshade_one_las(
        input_file=initial_las_file, output_dir=out_dir, config=config.mnx_dtm, type_raster="dtm"
    )

    # Step 2/2 : color
    add_color.color_raster_dtm_hillshade_with_LUT(
        input_initial_basename=initial_las_filename,
        input_raster=raster_DTM_hs_1M,
        output_dir=out_dir,
        list_c=list_cycles,
        dico_fld=dico_folder_modif,
    )

    # Map class color
    # Step 1/3 : DSM hillshade
    raster_DSM_hs = map_DXM.create_dxm_with_hillshade_one_las(
        input_file=initial_las_file, output_dir=out_dir, config=config.mnx_dsm, type_raster="dsm"
    )
    # Step 2/3 : create map fill gaps color
    raster_class_fgc = map_class.create_map_class(
        input_las=initial_las_file, output_dir=out_dir, dico_fld=dico_folder_modif, config=config.mnx_dsm
    )
    # Step 3/3 : fusion with MNS
    map_class.multiply_DSM_class(
        input_DSM=raster_DSM_hs,
        input_raster_class=raster_class_fgc,
        output_dir=output_dir_map_class_color,
        output_filename=initial_las_filename,
        output_extension=config.mnx_dsm.io.extension,
        bounds=bounds_las,
    )


if __name__ == "__main__":
    main()
