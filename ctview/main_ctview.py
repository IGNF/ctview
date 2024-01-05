import logging as log
import os

import hydra
from omegaconf import DictConfig

import ctview.map_class as map_class
import ctview.map_density as map_density
import ctview.map_DTM_DSM as map_DTM_DSM
import ctview.utils_pdal as utils_pdal
from ctview.utils_folder import create_folder, dico_folder_template


def get_las_liste(input_las, input_dir):
    """
    Extract list of las/laz file of the input (input_las with arg -i or input_dir with arg -idir
    Args :
        input_las : las in input (can be string or NoneType)
        input_dir : directory in input (can be string or NoneType)
    Return :
        las_list : list of las/laz (basename, not filename)
            ex : '/folder1/folder2/Semis_4145_5556_IGN69.las' -> ['Semis_4145_5556_IGN69.las']
    """
    las_list = []
    if input_las is None:
        for filename in os.listdir(input_dir):
            las_input_file = os.path.join(input_dir, filename)
            if os.path.isfile(las_input_file) & las_input_file.lower().endswith((".las", ".laz")):
                log.info(filename)
                las_list.append(filename)
    else:
        input_dir = os.path.dirname(input_las)
        filename = os.path.basename(input_las)
        las_input_file = input_las
        if os.path.isfile(las_input_file) & las_input_file.lower().endswith((".las", ".laz")):
            log.info(filename)
            las_list.append(filename)
        else:
            raise RuntimeError("-i arg is not a las/laz. For more info run the same command by adding --help")

    if len(las_list) == 0:
        raise RuntimeError("Erreur: Aucun fichier .las ou .laz dans le dossier: " + input_dir)

    return las_list, input_dir


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
    os.makedirs(output_dir_map_density)
    output_dir_map_class_color = os.path.join(out_dir, config.io.output_folder_map_class_color)
    os.makedirs(output_dir_map_class_color)
    output_dir_map_DTM_color = os.path.join(out_dir, config.io.output_folder_map_DTM_color)
    os.makedirs(output_dir_map_DTM_color)

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
    raster_DTM_dens = map_DTM_DSM.create_dxm_with_hillshade_one_las_XM(
        input_file=initial_las_file, output_dir=out_dir, config=config.mnx_dtm_dens, type_raster="dtm_dens"
    )
    # Step 2 : raster of density
    log.info("\nStep 2/3 : raster of density\n")
    raster_dens, success = map_density.generate_raster_of_density(
        input_las=initial_las_file, output_dir=out_dir, config=config.mnx_dtm_dens
    )
    # Step 3 : multiply density and DTM layers
    log.info("\nStep 3/3 : raster of density\n")
    if success:
        map_density.multiply_DTM_density(
            input_DTM=raster_DTM_dens,
            input_dens_raster=raster_dens,
            filename=initial_las_filename,
            output_dir=output_dir_map_density,
            config=config.mnx_dtm_dens,
            bounds=bounds_las,
        )
    else:
        log.warning(f"La dalle {initial_las_file} ne contient pas de points sol. Carte de densité non générée.")

    # DTM hillshade color
    # Step 1/2 : DTM hillshade
    raster_DTM_hs_1M = map_DTM_DSM.create_dxm_with_hillshade_one_las_XM(
        input_file=initial_las_file, output_dir=out_dir, config=config.mnx_dtm, type_raster="dtm"
    )

    # Step 2/2 : color
    map_DTM_DSM.color_raster_dtm_hillshade_with_LUT(
        input_initial_basename=initial_las_filename,
        input_raster=raster_DTM_hs_1M,
        output_dir=out_dir,
        list_c=list_cycles,
        dico_fld=dico_folder_modif,
    )

    # Map class color
    # Step 1/3 : DSM hillshade
    raster_DSM_hs = map_DTM_DSM.create_dxm_with_hillshade_one_las_XM(
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
