# Variables
BACKEND_IMAGE_NAME = maybee-backend
BACKEND_DOCKERFILE = ./Dockerfile
BACKEND_CONTAINER_NAME = maybee-backend
BACKEND_PORT = 8000

# Build the backend Docker image
build:
	docker build -t $(BACKEND_IMAGE_NAME) -f $(BACKEND_DOCKERFILE) .

install:
	poetry install


test:
	poetry run pytest -s -v

up:
	docker compose down
	docker compose up
