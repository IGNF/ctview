import fnmatch
import re
import os
import tempfile
import geojson

from osgeo import gdal, osr, ogr

DICO_CLASS = os.path.join("..","LUT","LUT_CLASS.txt")

# import lidarutils.geometry_utils as gu
# import lidarutils.gdal_utils as lu_gdal_utils


def add_epsg_to_raster(raster: str, epsg: int):
    """add epsg to raster"""
    gdal_image = gdal.Open(raster)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    gdal_image.SetProjection(srs.ExportToWkt())


def build_vrt(
    vrt: str, input_images_dir: str, format_image: str, epsg: int, force_if_exists: bool
):
    """build a vrt if non exists"""
    if not force_if_exists and os.path.exists(vrt):
        return

    # scan des fichiers
    images = []
    reobj = re.compile(fnmatch.translate("*." + format_image), re.IGNORECASE)
    for file in os.listdir(input_images_dir):
        if reobj.match(file):
            add_epsg_to_raster(input_images_dir + "/" + file, epsg)
            images.append(input_images_dir + "/" + file)

    vrt_options = gdal.BuildVRTOptions(resampleAlg="bilinear", addAlpha=False)
    my_vrt = gdal.BuildVRT(vrt, images, options=vrt_options)
    my_vrt = None


# def extract_from_vrt(in_vrt: str, out_put_image: str, bbox: gu.Bbox):
#     """extract part of DTM"""
#     gdal.Translate(
#         out_put_image, in_vrt, projWin=[bbox.xmin, bbox.ymax, bbox.xmax, bbox.ymin]
#     )


def get_box_from_image(input_raster: str):
    """get image bbox"""
    src = gdal.Open(input_raster)
    ulx, x_res, _, uly, _, y_res = src.GetGeoTransform()
    lrx = ulx + (src.RasterXSize * x_res)
    lry = uly + (src.RasterYSize * y_res)
    return gu.Bbox(ulx, lrx, lry, uly)


def rasterise(
    image_out: str, geo: str, image_ref_georef: str, type: gdal, options=None
):
    """rasterise a geometry"""
    data_src = gdal.Open(image_ref_georef)
    drv_tiff = gdal.GetDriverByName("GTiff")
    ds_out = drv_tiff.Create(
        image_out, data_src.RasterXSize, data_src.RasterYSize, 1, type
    )
    ds_out.SetGeoTransform(data_src.GetGeoTransform())
    if geo is not None and os.path.exists(geo):
        source_ds = ogr.Open(geo)
        source_layer = source_ds.GetLayer()
        if options:
            gdal.RasterizeLayer(ds_out, [1], source_layer, options=options)
        else:
            gdal.RasterizeLayer(ds_out, [1], source_layer, None)
    data_src, ds_out = None, None


def polygonize_and_add_field_name(raster_unvalide: str, epsg: int, field_name: str):
    unvalide_area = []
    out_json_density_ground = tempfile.NamedTemporaryFile(
        suffix="_polygonize_and_add_field_name.json"
    )
    lu_gdal_utils.gdal_polygonize(raster_unvalide, out_json_density_ground.name, epsg)
    with open(out_json_density_ground.name) as file:
        geo_json = geojson.load(file)
        features = geo_json["features"]
        for fea in features:
            fea["properties"]["type erreur"] = field_name
            unvalide_area.append(fea)
    return unvalide_area


def get_raster_corner_coord(in_raster: str):
    """
    Get corners coordinates from a raster
    Return :
        tuple(upper_left_x,upper_left_y,lower_right_x,lower_right_y)
        """
    gtif = gdal.Open(in_raster)
    ulx, xres, xskew, uly, yskew, yres  = gtif.GetGeoTransform()
    lrx = ulx + (gtif.RasterXSize * xres)
    lry = uly + (gtif.RasterYSize * yres)
    return (ulx,uly,lrx,lry)

def transform_CornerCoord_to_Bounds(corner_coord: tuple):
    """
    Transform corners coordinates to maximum and minimum x and y
    Warning : 
        corner_coord must be in this order : (upper_left_x,upper_left_y,lower_right_x,lower_right_y)
    Return :
        ([minx,maxx],[miny,maxy])
    """
    _X = [corner_coord[0],corner_coord[2]]
    _Y = [corner_coord[1],corner_coord[3]]

    _X.sort() # arrange in ascending order
    _Y.sort()

    return (_X,_Y)



def color_raster_by_class_2(input_raster, output_raster):
    "Color raster by classe"
    #   classif = "Classification[6:6]"  # classif 6 = batiments

    gdal.DEMProcessing(
        destName=output_raster,
        srcDS=input_raster,
        processing="color-relief",
        colorFilename=DICO_CLASS,
    )


def color_raster_with_LUT(input_raster, output_raster, LUT):
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
        processing="color-relief",
        colorFilename=LUT,
    )
