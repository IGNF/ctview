# Autor : Elucon

# IMPORT

import subprocess
import numpy
import logging as log
import os

# FONCTION


def get_zmin_zmax_from_DTM(input_DTM: str):
    """
    Get zmin and zmax of an DTM.
    input_DTM : path of the DTM
    """
    recupStat = subprocess.getstatusoutput("gdalinfo -stats " + input_DTM)

    info = recupStat[1]

    listLine = info.split("\n")

    zmin = 0
    zmax = 0

    for line in listLine:
        if "STATISTICS_MAXIMUM" in line:
            zmax = numpy.ceil(float(line.split("=")[1]))

        if "STATISTICS_MINIMUM" in line:
            zmintest = numpy.ceil(float(line.split("=")[1]))
            if zmintest > 0:
                zmin = zmintest

    log.info(f"Zmin :{zmin}")
    log.info(f"Zmax :{zmax}")

    return zmax, zmin


def generate_LUT_X_cycle(file_las: str, file_DTM: str, nb_cycle: int):
    """
    Generate a LUT in link with a DTM.
    file_las : points cloud
    file_MTN : DTM originate from the points cloud
    nb_cycle : the number of cycle that allows to generate the LUT
    return   : path of the LUT
    """

    log.info(f"Generate LUT of file {file_DTM}")

    path = os.path.join("LUT",f"LUT_{nb_cycle}cycle_{file_las[-31:-4]}.txt")

    zmin, zmax = get_zmin_zmax_from_DTM(input_DTM=file_DTM)

    DTM_LUTcycle_FILE = open(path, "w")

    DTM_LUTcycle_FILE.write(f"#LUT of {file_DTM}\n")
    DTM_LUTcycle_FILE.write(f"#number of cycles :{nb_cycle}\n")

    log.info(f"Number of cycles : {nb_cycle}")

    pasCycle = (zmax - zmin) / nb_cycle

    pasCouleur = (zmax - zmin) / (nb_cycle * 5)

    for c in range(nb_cycle):

        DTM_LUTcycle_FILE.write(str(round(zmin + c * pasCycle, 1)) + " 64 128 128\n")
        DTM_LUTcycle_FILE.write(
            str(round(zmin + c * pasCycle + pasCouleur, 1)) + " 255 255 0\n"
        )
        DTM_LUTcycle_FILE.write(
            str(round(zmin + c * pasCycle + 2 * pasCouleur, 1)) + " 255 128 0\n"
        )
        DTM_LUTcycle_FILE.write(
            str(round(zmin + c * pasCycle + 3 * pasCouleur, 1)) + " 128 64 0\n"
        )
        DTM_LUTcycle_FILE.write(
            str(round(zmin + c * pasCycle + 4 * pasCouleur, 1)) + " 240 240 240\n"
        )

    DTM_LUTcycle_FILE.close()

    return path


if __name__ == "__main__":

    generate_LUT_X_cycle(
        file_las="../LAS/C5_OK.las",
        file_DTM="../test_raster/DTM/C5_OK_DTM_hillshade.tif",
        nb_cycle=6,
    )
