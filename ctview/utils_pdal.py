import numpy as np
import pdal


def write_raster_class(
    input_points: np.array, output_raster: str, res: float, raster_driver: str, no_data_value: float
):
    """Generate a raster with the contained classes by interpolation of all points that fall
    in a resolution * sqrt(2) radius from the pixel centers.


    Args:
        input_points (np.array): Points of the input las (as read with a pdal.readers.las)
        output_raster (str): path to the output raster
        res (float): pixel size of the output raster
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)
        no_data_value (float): Value of pixel if contains no data
    """
    """ """
    pipeline = pdal.Writer.gdal(
        filename=output_raster,
        resolution=res,
        dimension="Classification",
        gdaldriver=raster_driver,
        nodata=no_data_value,
    ).pipeline(input_points)
    pipeline.execute()


def read_las_file(input_las: str):
    """Read a las file and put it in an array"""
    pipeline = pdal.Pipeline() | pdal.Reader.las(filename=input_las)
    pipeline.execute()
    return pipeline.arrays[0]


def get_info_from_las(points):
    """get info from a las to put it in an array"""
    pipeline = pdal.Filter.stats().pipeline(points)
    pipeline.execute()
    return pipeline.metadata


def get_bounds_from_las(in_las: str):
    """get bounds=([minx,maxx],[miny,maxy]) from las file"""
    metadata = get_info_from_las(read_las_file(in_las))
    xmin = metadata["metadata"]["filters.stats"]["bbox"]["native"]["bbox"]["minx"]
    xmax = metadata["metadata"]["filters.stats"]["bbox"]["native"]["bbox"]["maxx"]
    ymin = metadata["metadata"]["filters.stats"]["bbox"]["native"]["bbox"]["miny"]
    ymax = metadata["metadata"]["filters.stats"]["bbox"]["native"]["bbox"]["maxy"]
    return ([xmin, xmax], [ymin, ymax])
