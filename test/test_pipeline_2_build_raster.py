# Autor : ELucon
# Crée des raster .tif par classe

# IMPORTS

import pdal
import numpy as np



# VARIABLES

FILENAME = 'LAS/pont_route_OK.las'
LIST_CLASS = [1,2,3,4,5,6,9,17,64,65,66,202]
VERBOSE = False



# FONCTIONS

def select_classif(las_to_check):
    """Keep only the classification that are in the cloud"""
    LIST_CLASS_IN_LAS = []

    for CLASSIF in LIST_CLASS :
        # Check if the las file contains points with classification==CLASSIF
        pts_CLASSIF = np.where(las_to_check["Classification"] == CLASSIF, 1, 0)
        # Compte le nombre de points possèdant cette classification
        nb_pts_CLASSIF = np.count_nonzero(pts_CLASSIF == 1)
        # Si au moins un point possède la classification on conserve la classification
        if nb_pts_CLASSIF != 0 :
            LIST_CLASS_IN_LAS.append(CLASSIF)
        else :
            print(f"Aucun point de classe {CLASSIF} dans {FILENAME}.\n")
    
    return LIST_CLASS_IN_LAS

    

def read_las(file_las):
    """Read a las file and put it in an array"""
    pipeline = pdal.Pipeline() | pdal.Reader.las(filename=file_las)
    pipeline.execute()
    return pipeline.arrays[0]



def filter_las(points,i):
    
    
    classif = f"Classification[{i}:{i}]"  # classif 6 = batiments
    pipeline = (
        # sélection de la classe
        pdal.Filter.range(limits=classif).pipeline(points)
        
        # colorisation imposée au points de la classe
        | pdal.Filter.colorinterp(
            ramp = "blue_hue",
        )

        # écriture du raster
        | pdal.Writer.gdal(
            filename=f"raster/dtm_classif{i}.tif",
            gdaldriver="GTiff",
            output_type="all",
            resolution=0.5,
        )
    )      
    pipeline.execute()

    if VERBOSE :
        print("Success")       

    return pipeline.arrays[0]



def write(points,i):


    RESULT_FILENAME = f"LAS_create/Result_class{i}.las"

    pipeline = pdal.Writer.las(filename=RESULT_FILENAME, extra_dims="all").pipeline(points)
    pipeline.execute()
    if VERBOSE :
        print("Success")   


# MAIN

if __name__ == "__main__":

    

    points = read_las(FILENAME)
    list_class_in_las = select_classif(points)

    for k in list_class_in_las :

        if VERBOSE :
            print(f'Enter filter classe {k}')

        filtered_points = filter_las(points,k)

        if VERBOSE :
            print(f'Out filter classe {k}')

        if VERBOSE :
            print(f'Enter write classe {k}')

        write(filtered_points,k)

        if VERBOSE :
            print(f'Out write classe {k}\n')

            
        
    


        """ | pdal.Filter.colorization(
        dimensions="Red:1:255.0, Blue, Green::256.0",
        raster=f"raster/color_classif.tif",
    ) """

