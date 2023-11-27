# Autor : ELucon

import json
import logging as log
import os


def give_name_resolution_raster(size):
    """
    Give a resolution from raster

    Args:
        size (int): raster cell size

    Return:
        _size(str): resolution from raster for output's name
    """
    if float(size) == 1.0:
        _size = str("_1M")
    elif float(size) == 0.5:
        _size = str("_50CM")
    elif float(size) == 5.0:
        _size = str("_5M")
    else:
        _size = str(size)
    return _size


def repare_files(las_liste: str, input_dir):
    for filename in las_liste:
        f = open(os.path.join(input_dir, filename), "rb+")
        f.seek(6)
        f.write(bytes([17, 0, 0, 0]))
        f.close()
        log.info(f"fichier {filename} repare")


def convert_json_into_dico(config_file: str):
    """
    Translate json into dictionnary
    """
    with open(config_file, "r") as file_handler:
        dico_config = json.load(file_handler)

    return dico_config
