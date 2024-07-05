# v0.5.0
- refactor map_class to several files
- new functionalities:
  - Metadata:
    - new multilayer binary map of class
    - flattened classification map using aggregation rules + precedence
    - the classification map has colors and classes description stored as metadata
    - add vizualisation classification map (with hillshade from DSM)

# v0.4.2
- fix:
  - set nodata value for the gdal_calc function to the default value. Forcing nodata to 0 set every 0 value to nodata.

# v0.4.1
- fix:
  - nodata value from config in gdal_calc is ignored because it works on color Byte data. Set to 0 for coherence with empty map of density.

# v0.4.0
- new functionalities:
  - default config does not save intermediate files
  - continuous integration
- fix:
  - density: use same density map in main_ctView as in main_metadata
  - add option to gdal DEMprocessing to process hillshade on the sides as well (removes black lines)
  - fix multiplication with DTM
- dependencies:
  - update pdal to 2.6+, python to 3.10+
  - update ign-mnx to 1.0.2 fixing classification values issues
- refactor:
  - simplify config file
  - generate buffer point cloud only once in the beggining of the algo
  - add gdal driver to config
  - add one main function for each output of main_ctview (density, dtm and class_map)

# v0.3.0
- Lib ign-mnx : version 0.3.0 -> version 1.0.0
- Config : use hydra
- Docker : docker image is now made from local code instead of a clone of the repository
- Metadata : new map of density, independant of other views
- Function `gdal_calc` now called from package `osgeo_utils` instead of lib `lidarutils`.
- Refactor (lint all code).
- Refactor (clean useless code).

# v0.2.0
- Change of interpolation method (startin-laplace -> pdal-tin).
- Correct bug linked to `makedirs`` + use of folder architecture dictionary.
- Use of lib ign-mnx for dtm and dsm creation.

# v0.1.4
- Fonctional version.
