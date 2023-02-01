# Autor : ELucon


# IMPORT

# Library
import ctview.utils_pdal as utils_pdal
import os
import argparse
import shutil
import logging as log

# Parameters
from ctview.parameter import dico_folder, dico_param


# FONCTION


def delete_folder(dest_dir: str):
    """Delete folders "Intensity" if exist"""
    LAS_new_dir = os.path.join(dest_dir, dico_folder["folder_intensity"])
    if os.path.isdir(LAS_new_dir):
        shutil.rmtree(LAS_new_dir)


def create_folder(dest_dir: str):
    """Create folder "Intensity" if not exist"""
    LAS_new_dir = os.path.join(dest_dir, dico_folder["folder_intensity"])
    os.makedirs(LAS_new_dir, exist_ok=True)


def create_map_intensity(input_las, raster_intensity):

    # Read las
    in_points = utils_pdal.read_las(input_las)

    # Create raster of intensity
    utils_pdal.write_raster(
        input_points=in_points,
        output_raster=raster_intensity,
        dim="Intensity",
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-las", "--input_las")
    parser.add_argument("-o", "--output_dir")

    return parser.parse_args()


def main():

    log.basicConfig(level=log.INFO)

    log.info("INTENSITY")

    # Get las file, output directory and extension
    args = parse_args()
    input_las = args.input_las
    output_dir = args.output_dir
    extension = dico_param["raster_extension"]

    log.info(f"file : {os.path.basename(input_las)}")

    # Creation folder
    delete_folder(output_dir)
    create_folder(output_dir)
    # Path
    output_filename = os.path.join(
        output_dir,
        dico_folder["folder_intensity"],
        f"{os.path.splitext(os.path.basename(input_las))[0]}_INTENSITY{extension}",
        )

    # Creation raster intensity
    create_map_intensity(input_las, output_filename)

    if not os.path.exists(output_filename):
        log.warning("ERROR : raster of intensity not created")


if __name__ == "__main__":

    main()
