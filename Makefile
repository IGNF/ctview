
install:
	mamba env update -n ctview -f environment.yml

install-precommit:
	pre-commit install

testing:
	./ci/test.sh

##############################
# Docker
##############################

PROJECT_NAME=lidar_hd/ct_view
VERSION=`python -m ctview._version`
REGISTRY=docker-registry.ign.fr

docker-build:
	docker build -t ${PROJECT_NAME}:${VERSION} -f Dockerfile .

docker-test:
	docker run --rm -it ${PROJECT_NAME}:${VERSION} python -m pytest -s

docker-remove:
	docker rmi -f `docker images | grep ${PROJECT_NAME} | tr -s ' ' | cut -d ' ' -f 3`
	docker rmi -f `docker images -f "dangling=true" -q`

docker-deploy:
	docker login docker-registry.ign.fr -u svc_lidarhd
	docker tag ${PROJECT_NAME}:${VERSION} ${REGISTRY}/${PROJECT_NAME}:${VERSION}
	docker push ${REGISTRY}/${PROJECT_NAME}:${VERSION}