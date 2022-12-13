# Autor : ELucon

# IMPORT

    # File
import tools
    # Library
import pdal
from osgeo import gdal
import numpy as np
import subprocess
import startinpy
import os
from sys import argv
from multiprocessing import Pool, cpu_count


def main():    
    # Create the severals folder if not exists
    create_folder(argv[2])
    if 3 <= len(argv) <= 7: start_pool(*argv[1:])
    else: print("Error: Incorrect number of arguments passed. Returning.")

def create_folder(dest_folder: str):
    """Create the severals folders "DTM" and "_tmp" if not exist"""
    # Create folder "DTM"
    DTM_new_dir = os.path.join(dest_folder, 'DTM')
    if not os.path.isdir(DTM_new_dir):
        os.makedirs(DTM_new_dir)
    # Create folder "_tmp"
    tmp_new_dir = os.path.join(dest_folder, '_tmp')
    if not os.path.isdir(tmp_new_dir):
        os.makedirs(tmp_new_dir)

def start_pool(target_folder, src, filetype = 'las', postprocess = 0,
               size = 1, method = 'startin-Laplace'):
    """Assembles and executes the multiprocessing pool.
    The interpolation variants/export formats are handled
    by the worker function (ip_worker(mapped)).
    """
    fnames = listPointclouds(target_folder, filetype)
    cores = cpu_count()
    print(f"Found {cores} logical cores in this PC")
    num_threads = cores -1
    if CPU_LIMIT > 0 and num_threads > CPU_LIMIT:
        print(f"Limit CPU usage to {CPU_LIMIT} cores due to env var CPU_LIMIT")
        num_threads = CPU_LIMIT
    print("\nStarting interpolation pool of processes on the {}".format(
        num_threads) + " logical cores.\n")

    if len(fnames) == 0:
        print("Error: No file names were input. Returning."); return
    pre_map, processno = [], len(fnames)
    for i in range(processno):
        pre_map.append([src, int(postprocess), float(size),
                            target_folder, fnames[i].strip('\n'), method, filetype])
    p = Pool(cores -1)
    p.map(ip_worker, pre_map)
    p.close(); p.join()
    print("\nAll workers have returned.")




def filter_las_ground(fpath: str, src: str, file: str):
    """ Reads the LAS file and filter only grounds from LIDAR.

    Args:
        fpath (str) : directory of projet who contains LIDAR (Ex. "data")
        src (str): directory of work who contains the output files
        file (str): name of LIDAR tiles
    """
    dst = str("DTM".join([src, '/']))
    FileOutput = "".join([dst, "_".join([file[:-4], 'ground.las'])])
    information = {}
    information = {
    "pipeline": [
            {
                "type":"readers.las",
                "filename":fpath,
                "override_srs": "EPSG:2154",
                "nosrs": True
            },
            {
                "type":"filters.range",
                "limits":"Classification[2:2],Classification[66:66]"
            },
            {
                "type": "writers.las",
                "a_srs": "EPSG:2154",
                # "minor_version": 4,
                # "dataformat_id": 6,
                "filename": FileOutput
            }
        ]
    }
    ground = json.dumps(information, sort_keys=True, indent=4)
    print(ground)
    pipeline = pdal.Pipeline(ground)
    pipeline.execute()


def execute_startin(pts, res, origin, size):
    """Takes the grid parameters and the ground points. Interpolates
    either using the TIN-linear or the Laplace method. Uses a -9999 no-data value. 
    Fully based on the startin package (https://startinpy.readthedocs.io/en/latest/api.html)

    Args:
        pts : ground points clouds
        res(list): resolution in coordinates (1m x 1m OU 5m x 5m)
        origin(list): coordinate location of the relative origin (bottom left)
        size (int): raster cell size (1 000 km -> raster carré de 1 000km de côté)

    Returns:
        ras(list): Z interpolation
    """

    # # Startin 
    tin = startinpy.DT(); tin.insert(pts) # # Insert each points in the array of points (a 2D array)
    ras = np.zeros([res[1], res[0]]) # # returns a new array of given shape and type, filled with zeros
    # # Interpolate method
    method == 'startin-Laplace'
    def interpolant(x, y): return tin.interpolate_laplace(x, y)

    yi = 0
    for y in np.arange(origin[1], origin[1] + res[1] * size, size):
        xi = 0
        for x in np.arange(origin[0], origin[0] + res[0] * size, size):
            ch = tin.is_inside_convex_hull(x, y) # check is the point [x, y] located inside  the convex hull of the DT
            if ch == False:
                ras[yi, xi] = -9999 # no-data value
            else:
                tri = tin.locate(x, y) # locate the triangle containing the point [x,y]. An error is thrown if it is outside the convex hull
                if tri != [] and 0 not in tri:
                    ras[yi, xi] = interpolant(x, y)
                else: ras[yi, xi] = -9999 # no-data value
            xi += 1
        yi += 1
    return ras

def get_origin(las: str):
    """
    Returns the North-West coordinates of the las.
    Ex of file name : Semis_2021_0843_6521_LA93_IGN69.laz
    Detail :
        0843 = X coordinate in km
        6521 = Y coordinate in km
        LA93 = system of projection (Lambert93)
        IGN69 = altimetric system

    input :
        las : str : the name of the points cloud file
    output :
        int, int, str, str : X coord in km, Y coord in km, system of projection, altimetric system
    """
    # réécrire plus proprement en considérant ce qu'il y a entre chaque _ (tiret du 8)    
    return int(las[11:15]), int(las[16:20]), str(las[21:25]), str(las[26:31])



def do(verbose=False):

    import sys
    # Pour tester ce fichier de création de raster colorisé par classe après une interpolation
    in_las = sys.argv[1:][0]
    # Dossier dans lequel seront créés les fichiers
    path_workfolder = sys.argv[1:][1]

    in_las_name = in_las[-35:-4]



    # Fichier de sortie MNT brut
    out_dtm_raster = f"{path_workfolder}{in_las_name}_DTM.tif"

    # Extraction infos du las
    origin_x, origin_y, ProjSystem, AltiSystem = get_origin(in_las_name)

    if verbose :
        print(f"North-West X coordinate : {origin_x} km")
        print(f"North-West Y coordinate : {origin_x} km")
        print(f"System of projection : {ProjSystem}")
        print(f"Altimetric system : {AltiSystem}")

    # # Filtre les points sol de classif 2 et 66
    # tools.filter_las_version2(las,las_pts_ground)

    # # Interpole avec la méthode de Laplace
    # resolution = # in meters
    # origine = 
    # size = 1.0 # résolution du raster (raster cell size)
    # execute_startin(pts=las_pts_ground, res=resolution, origin=origin, size=size)



if __name__ == '__main__':
    
    do(True)