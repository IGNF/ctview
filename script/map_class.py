#Autor : ELucon

#IMPORT

import pdal
from osgeo import gdal
import tools



#FONCTION













# TEST

if __name__ == "__main__":

    import sys

    in_las = sys.argv[1:][0]
    # Read las
    in_points = tools.read_las(in_las)

    # Write raster
    output_raster = f'../test_raster/raster2_{in_las[7:-4]}.tif'
    tools.write_raster_class(in_points, output_raster)
    # Color
    color_raster = f'../test_raster/raster2_color_{in_las[7:-4]}.tif'
    tools.color_raster_by_class_2(output_raster, color_raster)
    

    # # Color
    # color_points = tools.color_points_by_class(in_points)
    # # Write raster
    # output_raster_color = f'../test_raster/raster_color{in_las[7:-4]}.tif'
    # tools.write_raster(color_points, output_raster_color)
    # output_raster = f'../test_raster/raster_{in_las[7:-4]}.tif'
    # tools.write_raster(in_points, output_raster)




