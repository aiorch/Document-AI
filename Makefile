APPLICATION_NAME ?= docaiapp

build:
	docker build --tag ${{ DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}\:$(github.sha ) .

push:
	docker push ${{ DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}\:${github.sha }


release:
	docker pull ${{ DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}\:${github.sha }
	docker tag  ${{ DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}\:${github.sha } ${{ DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}\:latest
	docker push ${{ DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}\:latest
