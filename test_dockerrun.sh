docker run \
-v /var/data/store-lidarhd/developpement/ctview/las/data0:/input \
-v /var/data/store-lidarhd/developpement/ctview/tests_local/test0:/output \
lidar_hd/ct_view \
python -m ctview.main -i /input/test_data_0000_0000_LA93_IGN69_ground.las -odir /output
