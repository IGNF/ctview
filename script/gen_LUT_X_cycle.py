#Autor : Elucon

# IMPORT

import subprocess
import numpy

# FONCTION


def get_zmin_zmax_from_MNT(
    input_MNT: str,
    verbose=False
):
    """
    Get zmin and zmax of an DTM.
    input_MNT : path of the DTM
    """
    recupStat = subprocess.getstatusoutput("gdalinfo -stats "+input_MNT)
    
    info = recupStat[1]
    
    listLine = info.split("\n")

    zmin = 0
    zmax = 0
    
    for line in listLine:
        if "STATISTICS_MAXIMUM" in line:
            zmax = numpy.ceil(float(line.split("=")[1]))
            
        if "STATISTICS_MINIMUM" in line:
            zmintest = numpy.ceil(float(line.split("=")[1]))
            if zmintest>0:
                zmin = zmintest
    
    if verbose :
        print(f"Zmin :{zmin}")
        print(f"Zmax :{zmax}")

    return zmax, zmin



def generate_LUT_X_cycle(
    file_las: str,
    file_MNT: str,
    nb_cycle: int,
    verbose=False
):
    """
    Generate a LUT in link with a DTM.
    file_las : points cloud 
    file_MTN : DTM originate from the points cloud
    nb_cycle : the number of cycle that allows to generate the LUT
    return   : path of the LUT
    """

    if verbose :
        print(f"\n\nGenerate LUT of file {file_MNT}")

    path = f"../LUT/LUT_{nb_cycle}cycle_{file_las[-31:-4]}.txt"

    zmin, zmax = get_zmin_zmax_from_MNT(input_MNT=file_MNT, verbose=verbose)

    MNT_LUTcycle_FILE = open(path, "w")
    
    MNT_LUTcycle_FILE.write(f"#LUT of {file_MNT}\n")
    MNT_LUTcycle_FILE.write(f"#number of cycles :{nb_cycle}\n")
    
    if verbose :
        print(f"Number of cycles : {nb_cycle}")

    pasCycle = (zmax - zmin) / nb_cycle
    
    pasCouleur = (zmax - zmin) / (nb_cycle * 5)
    
    for c in range(nb_cycle):
    
        MNT_LUTcycle_FILE.write(str(round(zmin+c*pasCycle,1))+" 64 128 128\n")
        MNT_LUTcycle_FILE.write(str(round(zmin+c*pasCycle+pasCouleur,1))+" 255 255 0\n")
        MNT_LUTcycle_FILE.write(str(round(zmin+c*pasCycle+2*pasCouleur,1))+" 255 128 0\n")
        MNT_LUTcycle_FILE.write(str(round(zmin+c*pasCycle+3*pasCouleur,1))+" 128 64 0\n")
        MNT_LUTcycle_FILE.write(str(round(zmin+c*pasCycle+4*pasCouleur,1))+" 240 240 240\n")
    
    
    MNT_LUTcycle_FILE.close()

    return path


if __name__=="__main__":

    generate_LUT_X_cycle(
        file_las = "../LAS/C5_OK.las",
        file_MNT = "../test_raster/DTM/C5_OK_DTM_hillshade.tif",
        nb_cycle = 6,
        verbose=True
    )