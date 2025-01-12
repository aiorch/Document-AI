GIT_HASH ?= $(shell git log --format="%h" -n 1)

DOCKER_USERNAME ?= litewavedev
APPLICATION_NAME ?= docaiapp

build:
        docker build --tag ${DOCKER_USERNAME}/${APPLICATION_NAME}\:$(GIT_HASH) .

push:
        docker push ${DOCKER_USERNAME}/${APPLICATION_NAME}\:${GIT_HASH}


release:
        docker pull ${DOCKER_USERNAME}/${APPLICATION_NAME}\:${GIT_HASH}
        docker tag  ${DOCKER_USERNAME}/${APPLICATION_NAME}\:${GIT_HASH} ${DOCKER_USERNAME}/${APPLICATION_NAME}\:latest
        docker push ${DOCKER_USERNAME}/${APPLICATION_NAME}\:latest
