# Makefile to manage main tasks
# cf. https://blog.ianpreston.ca/conda/python/bash/2020/05/13/conda_envs.html#makefile

# Oneshell means I can run multiple lines in a recipe in the same shell, so I don't have to
# chain commands together with semicolon
.ONESHELL:

install:
	mamba env update -n ctview -f environment.yml

install-precommit:
	pre-commit install

testing:
	python -m pytest -s ./test -v

##############################
# Docker
##############################

REGISTRY=ghcr.io
NAMESPACE=ignf
IMAGE_NAME=ctview
VERSION=`python -m ctview._version`
FULL_IMAGE_NAME=${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}

docker-build:
	docker build -t ${IMAGE_NAME}:${VERSION} -f Dockerfile .

docker-test:
	docker run --rm ${IMAGE_NAME}:${VERSION} python -m pytest -s -m "not functional_test"

docker-remove:
	docker rmi -f `docker images | grep ${IMAGE_NAME}:${VERSION} | tr -s ' ' | cut -d ' ' -f 3`

docker-deploy:
	docker tag ${IMAGE_NAME}:${VERSION} ${FULL_IMAGE_NAME}
	docker push ${FULL_IMAGE_NAME}