docker run --rm \
-v /var/data/store-lidarhd/developpement/ctview/las/data0b:/input \
-v /var/data/store-lidarhd/developpement/ctview/tests_local_docker/test0b:/output \
lidar_hd/ct_view \
python -m ctview.main -i /input/Semis_2021_0785_6378_LA93_IGN69_light.laz -odir /output
