# dev
- new:
  - default config does not save intermediate files for density
- dependencies: update pdal to 2.6+, python to 3.10+
- refactor: 
  - simplify config file
  - generate buffer point cloud only once in the beggining of the algo
  - add gdal driver to config
  - add one main function for each output of main_ctview (density, dtm and class_map)
-  fix: add option to gdal DEMprocessing to process hillshade on the sides as well (removes black lines)
- density:
  - use same density map in main_ctView as in main_metadata
  - fix multiplication with DTM
- new: continuous integration
- update ign-mnx to 1.0.2 fixing classification values issues

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
