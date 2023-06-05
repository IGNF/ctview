import pdal

FILENAME = 'pont_route_OK.las'
RESULT_FILENAME = "Result.las"


def read_las(file_las):
    """Read a las file and put it in an array"""
    pipeline = pdal.Pipeline() | pdal.Reader.las(filename=file_las)
    pipeline.execute()
    return pipeline.arrays[0]


def filter_las(points):
    classif = "Classification[6:6]"  # classif 6 = batiments
    pipeline = (
        pdal.Filter.range(limits=classif).pipeline(points)
        | pdal.Filter.hag_nn()
        | pdal.Filter.range(limits=classif)
    )
    pipeline.execute()
    return pipeline.arrays[0]


def write(points):
    pipeline = pdal.Writer.las(filename=RESULT_FILENAME, extra_dims="all").pipeline(points)
    pipeline.execute()

if __name__ == "__main__":

    

    points = read_las(FILENAME)
    filtered_points = filter_las(points)
    write(filtered_points)
