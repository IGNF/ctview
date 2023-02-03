# IMPORT

# Library
import argparse
import os
import logging as log
import sys
import shutil
import ctview.utils_tools as utils_tools
import ctview.utils_pdal as utils_pdal

# Internal function
import ctview.map_DTM_DSM as map_DTM_DSM
from ctview.parameter import dico_param
from ctview.utils_folder import create_folder, dico_folder
import ctview.map_density as map_density

# Parameters
extension = dico_param["raster_extension"]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", default=None)
    parser.add_argument("-odir", "--output_dir", default=None)
    parser.add_argument(
        "-m", "--interp_method", default=dico_param["interpolation_method"]
    )
    parser.add_argument(
        "-c",
        "--cycles_DTM_colored",
        nargs="+",
        type=int,
        default=dico_param["cycles_color_DTM"],
    )

    return parser.parse_args()


def main():

    log.basicConfig(level=log.INFO, format='%(message)s')

    # Get las file, output directory and interpolation method
    args = parse_args()
    in_las = args.input_file
    out_dir = args.output_dir
    interp_Method = args.interp_method
    list_cycles = args.cycles_DTM_colored

    in_dir = os.path.dirname(in_las)
    filename = os.path.basename(in_las)

    if os.path.exists(out_dir):
        # Clean folder test if exists
        shutil.rmtree(out_dir)
    else:
        # Create folder test if not exists
        os.makedirs(out_dir)

    # Create folders of dico_folder in out_dir
    create_folder(out_dir)

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
    # ## Step 3 : multiply density and DTM layers
    # map_density.multiply_DTM_density(
    #     input_DTM=raster_DTM_dens, 
    #     input_dens_raster=raster_dens, 
    #     filename=filename,
    #     output_dir=out_dir
    # )
    # DTM hillshade color
    map_DTM_DSM.create_map_one_las_DTM(
        input_las=os.path.join(in_dir, filename),
        output_dir=out_dir,
        interpMETHOD=interp_Method,
        list_c=list_cycles,
        type_raster="DTM"
    )
    # DSM hillshade
    map_DTM_DSM.create_map_one_las_DSM(
        input_las=os.path.join(in_dir, filename),
        output_dir=out_dir,
        interpMETHOD=interp_Method,
        type_raster="DSM"
    )


if __name__ == "__main__":

    main()
