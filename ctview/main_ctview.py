import argparse
import logging as log
import os

import ctview.map_class as map_class
import ctview.map_density as map_density
import ctview.map_DTM_DSM as map_DTM_DSM
import ctview.utils_pdal as utils_pdal
from ctview.parameter import dico_param
from ctview.utils_folder import (
    add_folder_list_cycles,
    create_folder,
    delete_empty_folder,
    dico_folder_template,
)

# Parameters
extension = dico_param["raster_extension"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", default=None, help="Must be a las/laz file.")
    parser.add_argument("-idir", "--input_dir", default=None, help="Directory which contains las/laz files.")
    parser.add_argument("-odir", "--output_dir", default=None, help="Output directory.")
    parser.add_argument(
        "-c",
        "--cycles_DTM_colored",
        nargs="+",
        type=int,
        default=dico_param["cycles_color_DTM"],
        help="""Allow to choose the number of coloration cycles for each colorisation.
        Exemple : -c 1 4 5 (3 colorisation with repectively 1, 4 and 5 cycles).""",
    )
    parser.add_argument(
        "-ofdens",
        "--output_folder_density",
        default=dico_folder_template["folder_density_final"],
        help="Output folder map density final.",
    )
    parser.add_argument(
        "-ofcc",
        "--output_folder_class_color",
        default=dico_folder_template["folder_CC_fusion"],
        help="Output folder map class color with DSM.",
    )
    parser.add_argument(
        "-ofcolor",
        "--output_folder_DTM_color",
        default=dico_folder_template["folder_DTM_color"],
        help="Output folder DTM color.",
    )

    return parser.parse_args()


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


def main():
    log.basicConfig(level=log.INFO, format="%(message)s")
    dico_folder_modif = dico_folder_template.copy()

    # Get las file, output directory and interpolation method
    args = parse_args()
    in_las = args.input_file
    in_dir = args.input_dir
    out_dir = args.output_dir
    list_cycles = args.cycles_DTM_colored
    # Change destination final folders
    log.debug(f"\n\ndico_folder BEFORE the user changes folder names on MAIN\n\n{dico_folder_modif}")
    dico_folder_modif["folder_density_final"] = args.output_folder_density
    dico_folder_modif["folder_CC_fusion"] = args.output_folder_class_color
    dico_folder_modif["folder_DTM_color"] = args.output_folder_DTM_color
    log.debug(f"\ndico_folder AFTER the user changes folder names on MAIN\n\n{dico_folder_modif}")

    # Add folders for all colorisations in dictionnary
    log.debug(f"\n\nBEFORE ADD folders in dico_folder_modif on MAIN\n\n{dico_folder_modif}")
    dico_folder_modif = add_folder_list_cycles(
        List=list_cycles,
        folder_base=dico_folder_modif["folder_DTM_color"],
        key_base="folder_DTM_color",
        dico_fld=dico_folder_modif,
    )
    log.debug(f"\nAFTER ADD folders in dico_folder_modif on MAIN\n\n{dico_folder_modif}")

    # Verify args are ok
    # input
    if in_las is None and in_dir is None:
        raise RuntimeError(
            "In input you have to give a las OR a directory. For more info run the same command by adding --help"
        )
    elif isinstance(in_las, str) and isinstance(in_dir, str):
        raise RuntimeError(
            "In input you can give a las OR a directory, not both. For more info run the same command by adding --help"
        )
    # output
    if out_dir is None:
        raise RuntimeError("No output directory. For more info run the same command by adding --help")

    # Create folder test if not exists
    os.makedirs(out_dir, exist_ok=True)

    # Create folders of dico_folder_modif in out_dir
    create_folder(out_dir, dico_fld=dico_folder_modif)

    # List las/laz
    las_liste, in_dir = get_las_liste(in_las, in_dir)

    # ## ACTIVATE IF NECESSARY
    # log.warning("#########")
    # log.warning("ATTENTION : modification LAS/LAZ file with function utils_tools.repare_file")
    # log.warning("#########")
    # utils_tools.repare_files(las_liste, in_dir)
    # time.sleep(2)

    for filename in las_liste:
        las_input_file = os.path.join(in_dir, filename)
        bounds_las = utils_pdal.get_bounds_from_las(las_input_file)  # get boundaries

        # DENSITY (DTM brut + density)
        # Step 1/3 : DTM brut
        raster_DTM_dens = map_DTM_DSM.create_dtm_with_hillshade_one_las_5M(
            input_file=las_input_file, output_dir=out_dir
        )
        # Step 2 : raster of density
        log.info("\nStep 2/3 : raster of density\n")
        raster_dens, success = map_density.generate_raster_of_density(input_las=las_input_file, output_dir=out_dir)
        # Step 3 : multiply density and DTM layers
        log.info("\nStep 3/3 : raster of density\n")
        if success:
            map_density.multiply_DTM_density(
                input_DTM=raster_DTM_dens,
                input_dens_raster=raster_dens,
                filename=filename,
                output_dir=out_dir,
                bounds=bounds_las,
                dico_fld=dico_folder_modif,
            )
        else:
            log.warning(f"La dalle {filename} ne contient pas de points sol. Carte de densité non générée.")

        # DTM hillshade color
        # Step 1/2 : DTM hillshade
        raster_DTM_hs_1M = map_DTM_DSM.create_dtm_with_hillshade_one_las_1M(
            input_file=las_input_file, output_dir=out_dir
        )

        # Step 2/2 : color
        map_DTM_DSM.color_raster_dtm_hillshade_with_LUT(
            input_initial_basename=filename,
            input_raster=raster_DTM_hs_1M,
            output_dir=out_dir,
            list_c=list_cycles,
            dico_fld=dico_folder_modif,
        )

        # Map class color
        # Step 1/3 : DSM hillshade
        raster_DSM_hs = map_DTM_DSM.create_dsm_with_hillshade_one_las_50CM(
            input_file=las_input_file, output_dir=out_dir
        )
        # Step 2/3 : create map fill gaps color
        raster_class_fgc = map_class.create_map_class(
            input_las=las_input_file, output_dir=out_dir, dico_fld=dico_folder_modif
        )
        # Step 3/3 : fusion with MNS
        map_class.multiply_DSM_class(
            input_DSM=raster_DSM_hs,
            input_raster_class=raster_class_fgc,
            filename=filename,
            output_dir=out_dir,
            bounds=bounds_las,
            dico_fld=dico_folder_modif,
        )

        # Delete folder
        delete_empty_folder(dir=out_dir)


if __name__ == "__main__":
    main()
