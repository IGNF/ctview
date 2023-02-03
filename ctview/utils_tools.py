# Autor : ELucon

# IMPORT
import os
import numpy as np


# FONCTION
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


def repare_files(las_dir: str):
    for f in os.listdir(las_dir):
        filename = os.path.join(las_dir, f)
        f = open(filename, "rb+")
        f.seek(6)
        f.write(bytes([17, 0, 0, 0]))
        f.close()
        print(f"fichier {filename} repare")


def sample(input_points):
    """Filtre points closest to 0.5m"""
    pipeline = pdal.Filter.sample(radius="0.5").pipeline(input_points)
    pipeline.execute()
    return pipeline.arrays[0]


def resample(input_las: str, res: float, output_filename: str):
    """Resample with a given resolution.
    Args :
        input_las : las file
        res : resolution in meter
    """
    pipeline = pdal.Reader.las(filename=input_las) | pdal.Writer.las(
        resolution=res,
        filename=output_filename,
        a_srs=f"EPSG:{EPSG}",
    )
    pipeline.execute()


def write_interp_table(output_filename: str, table_interp: np.ndarray):
    """Write table of interpolation on a text file
    Args :
        output_filename : directory of text file
        table_interp : table of interpolation
    """
    with open(output_filename, "w") as f:
        l, c = table_interp.shape
        s = ""
        for i in range(l):
            ligne = ""
            for j in range(c):
                ELEMENTtable = table_interp[i, j]
                ligne += f"{round(ELEMENTtable,5) : >20}"
            s += ligne
            s += ""

        f.write(s)
