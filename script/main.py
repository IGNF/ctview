# IMPORT

# Library
import argparse
import map_MNT
import os
import logging as log
import sys

# Internal function
import map_MNT_interp
from parameter import dico_param
from check_folder import delete_folder, create_folder

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-idir", "--input_dir", default=None)
    parser.add_argument('-odir', '--output_dir', default=None)
    parser.add_argument("-m", "--interp_method", default=dico_param["interpolation_method"])
    parser.add_argument("-c", "--cycles_MNT_colored", nargs="+", default=dico_param["cycles_color_DTM"])

    return parser.parse_args()

def main():

    log.basicConfig(level=log.INFO)

    # Get las file, output directory and interpolation method
    args = parse_args()
    in_dir = args.input_dir
    out_dir = args.output_dir
    interp_Method = args.interp_method
    list_cycles = args.cycles_MNT_colored

    try :
        list_cycles = list(map(int, list_cycles)) # all element are integers
    except ValueError :
        print("Error in -c argument. Integer expected for each element.")
        sys.exit()
    
    # Create output directory if not exist
    os.makedirs(out_dir, exist_ok=True)

    # Delete folders already in out_dir
    try :
        delete_folder(out_dir)
        create_folder(out_dir)
    except TypeError :
        log.error("Output directory is None. String expected.")
  
    # Scan las/laz file from input directory
    list_las = []
    for f in os.listdir(in_dir) :
        # Only look at file with las/laz extension
        if os.path.splitext(f)[1] in [".las", ".laz"] :
            list_las.append(f)
        
    # Print file founded
    log.info(f"{len(list_las)} las/laz founded :")
    for f in list_las :
        log.info(os.path.basename(f))

    # Scan las/laz file from input directory
    for f in list_las :
            
        log.info(f"FILE : {os.path.join(in_dir,f)}")

        map_MNT_interp.create_map_one_las(input_las = os.path.join(in_dir, f),
                            output_dir = out_dir,
                            interpMETHOD = interp_Method,
                            list_c = list_cycles)

if __name__=="__main__":

    main()
