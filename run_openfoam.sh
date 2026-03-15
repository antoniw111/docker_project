#!/bin/bash
# Helper script to start the OpenFOAM container

echo "Starting OpenFOAM 2.1.1 environment..."
echo "Your local 'docker_root' directory is mounted to '/home/openfoam/project' inside the container."
echo "You can exit the container by typing 'exit'."

# Ensure docker_root exists
mkdir -p docker_root

# Export UID and GID so docker-compose picks them up
export UID=$(id -u)
export GID=$(id -g)

# Build the image if it doesn't exist, and run an interactive shell
docker compose build
docker compose run --rm openfoam
