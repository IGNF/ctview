import pdal
import tempfile

from shapely.geometry import shape

from ctclass import utils_geometry, utils_gdal


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


def calc_boundary(points, size_hexbin_edge):
    """Calcul approximate boundary of points with hexbin"""
    if len(points) == 0:
        return None
    pipeline = pdal.Filter.hexbin(smooth=False, edge_size=size_hexbin_edge).pipeline(
        points
    )
    pipeline.execute()
    metadata_hexbin = pipeline.metadata["metadata"]["filters.hexbin"]
    if not "boundary_json" in metadata_hexbin:
        print(metadata_hexbin["error"])
        return None
    area = metadata_hexbin["boundary_json"]
    return shape(area)


def assign_classification(points):
    """assign classification to the entire las"""
    pipeline = pdal.Filter.assign(value="Classification = 0").pipeline(points)
    pipeline.execute()
    return pipeline.arrays[0]


def tab_class_to_str_pdal_class(class_filtre: [int]):
    """Build a string list for range filter classification"""
    tab_class = ""
    for c in class_filtre:
        tab_class += "Classification[" + str(c) + ":" + str(c) + "],"
    return tab_class[:-1]


def range_classification_points(points_ini, class_filtre: [int]):
    """range points with some class"""
    pipeline = pdal.Filter.range(
        limits=tab_class_to_str_pdal_class(class_filtre)
    ).pipeline(points_ini)
    pipeline.execute()
    return pipeline.arrays[0]


def filter_points_within_geom(points, geom: shape, class_filtre: [int]):
    def build_multipolygon_from_polygon_or_multipolygon(geo: shape):
        """Build a list of polygones from a geometry (polygon or multipolygon)"""
        poly_tab = []
        if geo.geom_type == "Polygon":
            poly_tab.append(geo)
        if geo.geom_type == "MultiPolygon":
            for poly in geo.geoms:
                poly_tab.append(poly)
        return poly_tab

    """filter points on a geometry"""
    poly_tab = build_multipolygon_from_polygon_or_multipolygon(geom)
    poly_tab_wkt = []
    for poly in poly_tab:
        poly_tab_wkt.append(poly.wkt)
    pipeline = pdal.Filter.range(
        limits=tab_class_to_str_pdal_class(class_filtre)
    ).pipeline(points) | pdal.Filter.crop(polygon=poly_tab_wkt)
    pipeline.execute()
    return pipeline.arrays[0]


def get_geom_non_open_ground(input_las: str):
    """Calcul geometry of non open area"""
    tab_ground_class = [
        1,
        2,
        17,
        66,
    ]  # classe d'objets au sol [unclassified, ground, ponts, points virtuel]
    tab_non_ground_class = []
    for i in range(1, 255):
        if i not in tab_ground_class:
            tab_non_ground_class.append(i)

    pipeline_non_ground = pdal.Reader.las(filename=input_las) | pdal.Filter.range(
        limits=tab_class_to_str_pdal_class(tab_non_ground_class)
    )
    pipeline_non_ground.execute()
    return calc_boundary(pipeline_non_ground.arrays[0], 1)


def get_ground_points_pipeline(input_las: str):
    """get ground or non classified with a height lower than 0.5"""
    tab_ground_class = [1, 2, 17, 66]
    pipeline = (
        pdal.Reader.las(filename=input_las)
        | pdal.Filter.range(limits=tab_class_to_str_pdal_class(tab_ground_class))
        | pdal.Filter.hag_nn()
        | pdal.Filter.range(limits="HeightAboveGround[0:0.5]")
    )
    return pipeline

def get_ground_points_only(input_las: str):
    """get ground or non classified with a height lower than 0.5"""
    tab_ground_class = [2]
    pipeline = (
        pdal.Reader.las(filename=input_las)
        | pdal.Filter.range(limits=tab_class_to_str_pdal_class(tab_ground_class))
        | pdal.Filter.hag_nn()
        | pdal.Filter.range(limits="HeightAboveGround[0:0.5]")
    )
    return pipeline


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
