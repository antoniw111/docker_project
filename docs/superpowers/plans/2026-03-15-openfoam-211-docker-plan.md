# OpenFOAM 2.1.1 Docker Configuration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a professional, single-stage Docker configuration to run a legacy OpenFOAM 2.1.1 environment with the `ddtFoam` solver on a modern host OS.

**Architecture:** Use `ubuntu:14.04` as a base image, install OpenFOAM 2.1.1 from the official repository, configure a non-root user matching the host UID/GID, copy the `ddtfoam-code` and compile it, and use `docker-compose.yml` to orchestrate the environment.

**Tech Stack:** Docker, Docker Compose, Bash, OpenFOAM 2.1.1, Ubuntu 14.04.

---

## Chunk 1: Docker Setup

### Task 1: Create the Dockerfile

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Write the Dockerfile**

Create the Dockerfile that sets up Ubuntu 14.04, installs dependencies, configures the repository, installs OpenFOAM 2.1.1, creates the user, and sets up the environment and compilation step for `ddtFoam`.

```dockerfile
# Use Ubuntu 14.04 (Trusty Tahr) for native GCC 4.8 compatibility with OpenFOAM 2.1.1
FROM ubuntu:14.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install essential tools and add OpenFOAM repository
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    curl \
    build-essential \
    flex \
    bison \
    zlib1g-dev \
    openmpi-bin \
    libopenmpi-dev \
    && sh -c "wget -O - http://dl.openfoam.org/gpg.key | apt-key add -" \
    && add-apt-repository http://dl.openfoam.org/ubuntu \
    && apt-get update \
    && apt-get install -y openfoam211 \
    && rm -rf /var/lib/apt/lists/*

# Build arguments for user mapping
ARG USER_ID
ARG GROUP_ID
ARG USER_NAME=openfoam

# Create a non-root user with the same UID/GID as the host user
RUN groupadd -g ${GROUP_ID} ${USER_NAME} && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -m -s /bin/bash ${USER_NAME}

# Set up the OpenFOAM environment for the user
RUN echo "source /opt/openfoam211/etc/bashrc" >> /home/${USER_NAME}/.bashrc

# Switch to the new user
USER ${USER_NAME}
WORKDIR /home/${USER_NAME}

# Define the user directory for OpenFOAM
ENV WM_PROJECT_USER_DIR=/home/${USER_NAME}/OpenFOAM/${USER_NAME}-2.1.1

# Create the user directory structure
RUN mkdir -p ${WM_PROJECT_USER_DIR}

# Copy the ddtfoam-code into the container
# Ensure the directory exists in the build context
COPY --chown=${USER_ID}:${GROUP_ID} ddtfoam-code ${WM_PROJECT_USER_DIR}/ddtfoam-code

# Compile ddtFoam
# Source the OpenFOAM environment and run Allwmake
RUN /bin/bash -c "source /opt/openfoam211/etc/bashrc && cd ${WM_PROJECT_USER_DIR}/ddtfoam-code && ./Allwmake"

# Default command: open a bash shell
CMD ["/bin/bash"]
```

- [ ] **Step 2: Commit**

```bash
git add Dockerfile
git commit -m "feat: create Dockerfile for OpenFOAM 2.1.1 and ddtFoam"
```

### Task 2: Create Docker Compose configuration

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Write the docker-compose.yml**

```yaml
version: '3.8'

services:
  openfoam:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - USER_ID=${UID:-1000}
        - GROUP_ID=${GID:-1000}
    volumes:
      - ./docker_root:/home/openfoam/project
    working_dir: /home/openfoam/project
    # Use interactive shell
    stdin_open: true
    tty: true
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add docker-compose orchestration"
```

### Task 3: Create Entrypoint Helper Script (Optional but recommended for ease of use)

**Files:**
- Create: `run_openfoam.sh`

- [ ] **Step 1: Write the helper script**

```bash
#!/bin/bash
# Helper script to start the OpenFOAM container

echo "Starting OpenFOAM 2.1.1 environment..."
echo "Your local 'docker_root' directory is mounted to '/home/openfoam/project' inside the container."
echo "You can exit the container by typing 'exit'."

# Ensure docker_root exists
mkdir -p docker_root

# Export UID and GID so docker-compose picks them up (important for Mac/some Linux setups)
export UID=$(id -u)
export GID=$(id -g)

# Build the image if it doesn't exist, and run an interactive shell
docker compose build
docker compose run --rm openfoam
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x run_openfoam.sh
```

- [ ] **Step 3: Commit**

```bash
git add run_openfoam.sh
git commit -m "feat: add run_openfoam helper script"
```
