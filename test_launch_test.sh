## clean store
rm -rf /var/data/store-lidarhd/developpement/ctview/tests_local_docker/test0/
rm -rf /var/data/store-lidarhd/developpement/ctview/tests_local_docker/test0b/
rm -rf /var/data/store-lidarhd/developpement/ctview/tests_local/test0/
rm -rf /var/data/store-lidarhd/developpement/ctview/tests_local/test0b/

## launch tests
./test_main_0.sh
./test_main_0b.sh
./test_main_docker_0.sh
./test_main_docker_0b.sh
