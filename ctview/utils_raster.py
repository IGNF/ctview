import logging as log
import rasterio
import numpy as np
import ctview.utils_pcd as utils_pcd
from collections.abc import Iterable


def generate_raster_raw(
    input_points: np.array,
    input_classifs: np.array,
    output_tif: str,
    epsg: int | str,
    fn: callable,
    classes_by_layer: list = [[]],
    tile_size: int = 1000,
    pixel_size: float = 1,
    buffer_size: float = 0,
    no_data_value: int = -9999,
    raster_driver: str = "GTiff",
):
    """Generate a (multilayer) raster of [something dependent of the function fn] for the classes in `class_by_layer`.

    The output has one layer per value in the classes_by_layer list.
    Each layer contains a [something dependent of the function fn] map for the classes listed in its correspondig list of
    values in classes_by_layer.
    Eg, if classes_by_layer = [[1, 2], [3], []]:
    * the first layer contains the [something dependent of the function fn] map for classes 1 and 2 commbined
    * the second layer contains the [something dependent of the function fn] map for class 3 only,
    * the last layer contains the [something dependent of the function fn] for all classes together

    Args:
        input_points (np.array): numpy array with the input points
        input_classifs (np.array): numpy array with classifications of the input points
        output_tif (str): path to the output file
        epsg (int): spatial reference of the output file
        classes_by_layer (list, optional): _description_. Defaults to [[]].
        tile_size (int, optional): size ot the raster tile in meters. Defaults to 1000.
        pixel_size (float, optional): pixel size of the output raster. Defaults to 1.
        buffer_size (float, optional): size of the buffer that has been added to the input points.
        (used to detect the raster corners) Defaults to 0.
        no_data_value (int, optional): No data value of the output. Defaults to -9999.
        raster_driver (str): raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers). Defaults to "GTiff"
    """
    if not isinstance(classes_by_layer, Iterable):
        raise TypeError(
            "In generate_raster_of_density, classes_by_layer is expected to be a list, "
            f"got {type(classes_by_layer)} instead)"
        )
    if not np.all([isinstance(item, Iterable) for item in classes_by_layer]):
        raise TypeError(
            "In generate_raster_of_density, classes_by_layer is expected to be a list of lists, "
            f"got {classes_by_layer} instead)"
        )

    pcd_origin_x, pcd_origin_y = utils_pcd.get_pointcloud_origin(input_points, tile_size, buffer_size)

    raster_origin = (pcd_origin_x - pixel_size / 2, pcd_origin_y + pixel_size / 2)

    rasters = []
    for classes in classes_by_layer:
        if classes:
            filtered_points = input_points[np.isin(input_classifs, classes), :]
        else:
            filtered_points = input_points

        rasters.append(fn(filtered_points, raster_origin, tile_size, pixel_size))

    rasters = np.array(rasters)
    with rasterio.Env():
        with rasterio.open(
            output_tif,
            "w",
            driver=raster_driver,
            height=rasters.shape[1],
            width=rasters.shape[2],
            count=rasters.shape[0],
            dtype=rasterio.float32,
            crs=f"EPSG:{epsg}" if str(epsg).isdigit() else epsg,
            transform=rasterio.transform.from_origin(raster_origin[0], raster_origin[1], pixel_size, pixel_size),
            nodata=no_data_value,
        ) as out_file:
            out_file.write(rasters.astype(rasterio.float32))

    log.debug(f"Saved to {output_tif}")
