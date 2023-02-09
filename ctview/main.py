# IMPORT

# Library
import argparse
import os
import logging as log
import ctview.utils_tools as utils_tools
import time

# Internal function
import ctview.map_DTM_DSM as map_DTM_DSM
from ctview.parameter import dico_param
from ctview.utils_folder import create_folder, dico_folder
import ctview.map_density as map_density

# Parameters
extension = dico_param["raster_extension"]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", default=None, help="Must be a las/laz file.")
    parser.add_argument("-idir", "--input_dir", default=None, help="Directory which contains las/laz files.")
    parser.add_argument("-odir", "--output_dir", default=None, help="Output directory.")
    parser.add_argument(
        "-m", "--interp_method", default=dico_param["interpolation_method"], help="Optional. Laplace method by default."
    )
    parser.add_argument(
        "-c",
        "--cycles_DTM_colored",
        nargs="+",
        type=int,
        default=dico_param["cycles_color_DTM"],
        help="Allow to choose the number of coloration cycles for each colorisation. Exemple : -c 1 4 5 (3 colorisation with repectively 1 cycle, 4 cycles and 5 cycles)."
    )

    return parser.parse_args()


def get_las_liste(input_las, input_dir):
    """
    Extract list of las/laz file of the input (input_las with arg -i or input_dir with arg -idir
    Args :
        input_las : las in input (can be string or NoneType)
        input_dir : directory in input (can be string or NoneType)
    Return :
        las_list : list of las/laz (basename, not filename) ex : '/folder1/folder2/Semis_4145_5556_IGN69.las' -> ['Semis_4145_5556_IGN69.las']
    """
    las_list = []
    if input_las==None :
        for filename in os.listdir(input_dir):
            las_input_file = os.path.join(input_dir, filename)
            if os.path.isfile(las_input_file) & las_input_file.lower().endswith(
                (".las", ".laz")
            ):
                log.info(filename)
                las_list.append(filename)
    else : 
        input_dir = os.path.dirname(input_las)
        filename = os.path.basename(input_las)
        las_input_file = input_las
        if os.path.isfile(las_input_file) & las_input_file.lower().endswith(
            (".las", ".laz")
        ):
            log.info(filename)
            las_list.append(filename)
        else :
            raise RuntimeError("-i arg is not a las/laz. For more info run the same command by adding --help")

    if len(las_list) == 0:
        raise RuntimeError(
            "Erreur: Aucun fichier .las ou .laz dans le dossier: " + input_dir
        )

    return las_list, input_dir

def main():

    log.basicConfig(level=log.INFO, format='%(message)s')

    # Get las file, output directory and interpolation method
    args = parse_args()
    in_las = args.input_file
    in_dir = args.input_dir
    out_dir = args.output_dir
    interp_Method = args.interp_method
    list_cycles = args.cycles_DTM_colored

    # Verify args are ok
    # input
    if (in_las==None and in_dir==None) :
        raise RuntimeError("In input you have to give a las OR a directory. For more info run the same command by adding --help")
    elif (isinstance(in_las,str) and isinstance(in_dir, str)) :
        raise RuntimeError("In input you can give a las OR a directory, not both ! For more info run the same command by adding --help")
    # output
    if (out_dir==None) :
        raise RuntimeError("No output directory. For more info run the same command by adding --help")

    # Create folder test if not exists
    os.makedirs(out_dir, exist_ok=True)

    # Create folders of dico_folder in out_dir
    create_folder(out_dir)

    # List las/laz
    las_liste, in_dir = get_las_liste(in_las, in_dir)

    # ## ACTIVATE IF NECESSARY
    # log.warning("#########")
    # log.warning("ATTENTION : modification LAS/LAZ file with function utils_tools.repare_file")
    # log.warning("#########")
    # utils_tools.repare_files(las_liste, in_dir)
    # time.sleep(2)

    for filename in las_liste :
        
        ## DENSITY (DTM brut + density)
        ## Step 1 : DTM brut
        raster_DTM_dens = map_DTM_DSM.create_map_one_las_DTM_dens(
            input_las=os.path.join(in_dir, filename),
            output_dir=out_dir,
            interpMETHOD=interp_Method,
            type_raster="DTM_dens"
        )
        ## Step 2 : raster of density
        raster_dens = map_density.generate_raster_of_density(
            input_las=os.path.join(in_dir, filename),
            output_dir=out_dir
        )
        ## Step 3 : multiply density and DTM layers
        map_density.multiply_DTM_density(
            input_DTM=raster_DTM_dens, 
            input_dens_raster=raster_dens, 
            filename=filename,
            output_dir=out_dir
        )
        # ## DTM hillshade color
        # map_DTM_DSM.create_map_one_las_DTM(
        #     input_las=os.path.join(in_dir, filename),
        #     output_dir=out_dir,
        #     interpMETHOD=interp_Method,
        #     list_c=list_cycles,
        #     type_raster="DTM"
        # )
        # ## DSM hillshade
        # map_DTM_DSM.create_map_one_las_DSM(
        #     input_las=os.path.join(in_dir, filename),
        #     output_dir=out_dir,
        #     interpMETHOD=interp_Method,
        #     type_raster="DSM"
        # )


if __name__ == "__main__":

    main()
