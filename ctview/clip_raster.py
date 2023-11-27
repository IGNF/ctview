from osgeo import gdal


def crop_raster(input_raster: str, output_raster: str, bounds: str):
    """
    Crop a raster with bounds extract from las at the origin of the raster.
    Args :
        input_raster : raster to crop
        output_raster : filename of raster that will be croped
        bounds : ([minx,maxx],[miny, maxy])
    """
    ulx = bounds[0][0]  # upper-left x = minx
    uly = bounds[1][1]  # upper-left y = maxy
    lrx = bounds[0][1]  # lower-right x = maxx
    lry = bounds[1][0]  # lower-right y = miny

    window = (ulx, uly, lrx, lry)

    gdal.Translate(srcDS=input_raster, destName=output_raster, projWin=window)


def clip_raster(input_raster: str, output_raster: str, bounds: str):
    minX, minY, maxX, maxY = bounds[0][0], bounds[1][0], bounds[0][1], bounds[1][1]
    RasterFormat = "GTiff"
    gdal.Warp(output_raster, input_raster, format=RasterFormat, outputBounds=[minX, minY, maxX, maxY])

    return output_raster
