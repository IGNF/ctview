docker run \
-v `pwd`/data/las:/input \
-v `pwd`/test_raster/aa_poubelletest/:/output \
lidar_hd/ct_view \
python -m ctview.main -i /input/test_data_0000_0000_LA93_IGN69_ground.las -odir /output
