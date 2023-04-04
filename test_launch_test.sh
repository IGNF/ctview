## clean store
rm -rf /var/data/store-lidarhd/developpement/ctview/1_tests_local/test0/
rm -rf /var/data/store-lidarhd/developpement/ctview/1_tests_local/test0b/
rm -rf /var/data/store-lidarhd/developpement/ctview/2_tests_local_docker/test0/
rm -rf /var/data/store-lidarhd/developpement/ctview/2_tests_local_docker/test0b/

## launch tests
./test_main_0_small_1dalle.sh
./test_main_0b_water_1dalle.sh
./test_docker/test_main_docker_0_small_1dalle.sh
./test_docker/test_main_docker_0b_water_1dalle.sh
