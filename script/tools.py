#Autor : ELucon

# IMPORT
import pdal
from osgeo import gdal

DICO_CLASS = "../dico/dictionnary_alamano.txt"
DICO_TEST = "../dico/ramp.txt"







# FONCTION

def read_las(file_las):
    """Read a las file and put it in an array"""
    pipeline = pdal.Pipeline() | pdal.Reader.las(filename=file_las)
    pipeline.execute()
    return pipeline.arrays[0]

def write_las(input_points, output_las):
    """Write a las file"""
    pipeline = pdal.Writer.las(filename = output_las).pipeline(input_points)
    pipeline.execute()

def write_raster(input_points, output_raster, dim):
    """
    Generate a raster.
    input_points : input
    output_raster : output
    dim : dimension
    """
    pipeline = pdal.Writer.gdal(
        filename=output_raster, 
        resolution=0.5,
        dimension=dim,
        ).pipeline(input_points)
    pipeline.execute()


def write_raster_z(input_points, output_raster):
    """Generate a raster"""
    pipeline = pdal.Writer.gdal(
        filename=output_raster, 
        resolution=0.5,
        dimension='Z'
        ).pipeline(input_points)
    pipeline.execute()

def write_raster_class(input_points, output_raster):
    """Generate a raster"""
    pipeline = pdal.Writer.gdal(
        filename=output_raster, 
        resolution=0.5,
        dimension="Classification",
        gdaldriver = 'GTiff',
        ).pipeline(input_points)
    pipeline.execute()


def filter_las(points, classif):
    """Filter with the classification classif"""
    classif = f"Classification[{classif}:{classif}]"  # classif 6 = batiments
    pipeline = (
        pdal.Filter.range(limits=classif).pipeline(points)
        | pdal.Filter.hag_nn()
        | pdal.Filter.range(limits=classif)
    )
    pipeline.execute()
    return pipeline.arrays[0]


def color_points_by_class(input_points) :
    "Color las points by class."
 #   classif = "Classification[6:6]"  # classif 6 = batiments
    pipeline = (
        pdal.Filter.colorinterp(
            ramp="pestel_shades",
            mad="true",
            k="1.8",
            dimension="Z",
            ).pipeline(input_points)
    )
    pipeline.execute()
    return pipeline.arrays[0]


def color_raster_by_class_2(input_raster, output_raster) :
    "Color raster by classe"
 #   classif = "Classification[6:6]"  # classif 6 = batiments
    
    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing = "color-relief",
        colorFilename = DICO_CLASS,
        )

def color_raster_with_LUT(input_raster, output_raster, LUT) :
    """
    Color raster with a LUT
    input_raster : path of raster to colorise
    output_raster : path of raster colorised
    dim : dimension to color
    LUT : dictionnary of color
    """
    
    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing = "color-relief",
        colorFilename = LUT,
        )







