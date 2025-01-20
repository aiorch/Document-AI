GIT_HASH ?= $(shell git log --format="%h" -n 1)

APPLICATION_NAME ?= docaiapp

build:
	docker build --tag ${DOCKER_REGISTRY_USER}/${APPLICATION_NAME}\:$(GIT_HASH) .

push:
	docker push ${DOCKER_REGISTRY_USER}/${APPLICATION_NAME}\:${GIT_HASH}


release:
	docker pull ${DOCKER_REGISTRY_USER}/${APPLICATION_NAME}\:${GIT_HASH}
	docker tag  ${DOCKER_REGISTRY_USER}/${APPLICATION_NAME}\:${GIT_HASH} ${DOCKER_USERNAME}/${APPLICATION_NAME}\:latest
	docker push ${DOCKER_REGISTRY_USER}/${APPLICATION_NAME}\:latest
