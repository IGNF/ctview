#Autor : ELucon


#IMPORT

import tools



#FONCTION


def create_map_intensity(input_las, raster_intensity):

    # Read las
    in_points = tools.read_las(input_las)

    # Create raster of intensity
    tools.write_raster(
        input_points=in_points,
        output_raster=raster_intensity,
        dim="Intensity",
        )



if __name__ == "__main__":

    import sys
    # Pour tester ce fichier de création de raster d'intensité 
    in_las = sys.argv[1:][0]

    # Chemins des fichiers raster
    raster_of_intensity = f"../test_raster/intensity/{in_las[7:-4]}_intensity.tif"

    # Création des rasters
    create_map_intensity(in_las, raster_of_intensity)
