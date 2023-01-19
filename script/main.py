# IMPORT

# Library
import argparse
import os
import logging as log
import sys
import shutil

# Internal function
import map_MNT_interp
from parameter import dico_param
from check_folder import create_folder


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-idir", "--input_dir", default=None)
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

    log.basicConfig(level=log.INFO)

    # Get las file, output directory and interpolation method
    args = parse_args()
    in_dir = args.input_dir
    out_dir = args.output_dir
    interp_Method = args.interp_method
    list_cycles = args.cycles_DTM_colored

    if os.path.exists(out_dir):
        # Clean folder test if exists
        shutil.rmtree(out_dir)
    else:
        # Create folder test if not exists
        os.makedirs(out_dir)

    # CReate folders of dico_folder in out_dir
    create_folder(out_dir)

    # Scan las/laz file from input directory
    list_las = []
    for f in os.listdir(in_dir):
        # Only look at file with las/laz extension
        if os.path.splitext(f)[1] in [".las", ".laz"]:
            list_las.append(f)

    # Print file founded
    log.info(f"{len(list_las)} las/laz founded :\n")
    for f in list_las:
        log.info(os.path.basename(f))

    # Scan las/laz file from input directory
    cpt=0
    for f in list_las:

        cpt += 1
        log.info(f"FILE {cpt}/{len(list_las)}: {f}\n\n")

        map_MNT_interp.create_map_one_las(
            input_las=os.path.join(in_dir, f),
            output_dir=out_dir,
            interpMETHOD=interp_Method,
            list_c=list_cycles,
            type_raster="DTM_dens"
        )

        map_MNT_interp.create_map_one_las(
            input_las=os.path.join(in_dir, f),
            output_dir=out_dir,
            interpMETHOD=interp_Method,
            list_c=list_cycles,
            type_raster="DTM"
        )

        map_MNT_interp.create_map_one_las(
            input_las=os.path.join(in_dir, f),
            output_dir=out_dir,
            interpMETHOD=interp_Method,
            list_c=list_cycles,
            type_raster="DSM"
        )


if __name__ == "__main__":

    main()
