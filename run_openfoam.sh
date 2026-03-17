#!/bin/bash
# Helper script to start the OpenFOAM container

echo "Starting OpenFOAM 2.1.1 and Cantera environments..."
echo "Your local 'docker_root' directory is mounted to '/home/openfoam/project' inside the container."
echo "You can exit the container by typing 'exit'."

# Ensure docker_root exists
mkdir -p docker_root

# Build the image if it doesn't exist, and run an interactive shell
docker compose up -d 
printf "To use openfoam with ddtFoam:\n docker compose exec openfoam bash\n"
printf "To use cantera:\n docker compose exec cantera bash\n"
printf "To stop them:\n docker compose stop\n"
printf "To stop end remove:\n docker compose down\n"
