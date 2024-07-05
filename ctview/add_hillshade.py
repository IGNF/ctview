from osgeo import gdal


def add_hillshade_one_raster(input_raster: str, output_raster: str):
    """Add hillshade to raster
    Arg :
        input_raster : input file with complete path
        output_raster : output file with complete path
    """
    gdal.DEMProcessing(destName=output_raster, srcDS=input_raster, processing="hillshade", computeEdges=True)
