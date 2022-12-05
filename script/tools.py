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

def write_raster_z(input_points, output_raster):
    """Generate a raster"""
    pipeline = pdal.Writer.gdal(
        filename=output_raster, 
        resolution=0.5,
        doimension='Z'
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


def build_dtm_from_points(
    points, output_dtm: str, epsg: int, dtm_type: str, resolution: float
):
    """build a dtm from points - dtm_type (min, max, mean)"""
    pipeline = pdal.Writer.gdal(
        filename=output_dtm,
        resolution=resolution,
        output_type=dtm_type,
        where="(Classification == 2 || Classification == 66)",
        data_type="Float32",
    ).pipeline(points)
    pipeline.execute()
    utils_gdal.add_epsg_to_raster(output_dtm, epsg)


def build_dtm_from_las(
    input_las: str, output_dtm: str, epsg: int, dtm_type: str, resolution: float
):
    """build a dtm from las - dtm_type (min, max, mean)"""
    points_ini = read_las_file(input_las)
    return build_dtm_from_points(points_ini, output_dtm, epsg, dtm_type, resolution)





