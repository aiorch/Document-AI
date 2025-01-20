APPLICATION_NAME ?= docaiapp

build:
	docker build --tag ${DOCKER_REGISTRY_USER}/${APPLICATION_NAME}:${GITHUB_SHA} .

push:
	docker push ${DOCKER_REGISTRY_USER}/${APPLICATION_NAME}:${GITHUB_SHA}


release:
	docker pull ${DOCKER_REGISTRY_USER}/${APPLICATION_NAME}:${GITHUB_SHA}
	docker tag  ${DOCKER_REGISTRY_USER}/${APPLICATION_NAME}:${GITHUB_SHA} ${DOCKER_USERNAME}/${APPLICATION_NAME}:latest
	docker push ${DOCKER_REGISTRY_USER}/${APPLICATION_NAME}:latest
