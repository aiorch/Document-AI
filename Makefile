APPLICATION_NAME ?= docaiapp

build:
	docker build --tag ${{ env.DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}:${ GITHUB_SHA } .

push:
	docker push ${{ env.DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}:${ GITHUB_SHA }


release:
	docker pull ${{ env.DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}:${GITHUB_SHA }
	docker tag  ${{ env.DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}:${GITHUB_SHA } ${{ env.DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}:latest
	docker push ${{ env.DOCKER_REGISTRY_USER }}/${APPLICATION_NAME}:latest
