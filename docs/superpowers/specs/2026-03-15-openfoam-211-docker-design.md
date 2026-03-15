# OpenFOAM 2.1.1 Docker Configuration for ddtFoam

## Goal
Create a professional, single-stage Docker configuration to run a legacy OpenFOAM 2.1.1 environment with the `ddtFoam` solver on a modern host OS. The configuration must be optimized for layers and ensure proper user file permissions.

## Architecture & Components

### 1. Base Image & Dependencies
*   **Base Image:** `ubuntu:14.04` (Trusty Tahr). This provides the native, stable environment (GCC 4.8) required by OpenFOAM 2.1.1, avoiding complex and fragile source compilations on modern systems.
*   **Dependencies:** Essential build tools (`build-essential`, `flex`, `bison`, `zlib1g-dev`), OpenMPI, and `wget`/`software-properties-common` for adding repositories.

### 2. OpenFOAM Installation
*   **Method:** Install `openfoam211` directly from the OpenFOAM Foundation repository (`http://dl.openfoam.org/ubuntu`) for maximum stability and speed.
*   **Configuration:** The global `.bashrc` or the dedicated user's `.bashrc` will automatically source `/opt/openfoam211/etc/bashrc` (note: the repository path is typically `/opt/`, not `/usr/lib/`, but we will verify this or link it).

### 3. User Mapping & Security
*   **Problem:** Files created inside a default Docker container are owned by `root`, making them uneditable on the host machine.
*   **Solution:** Create a non-root user (e.g., `openfoam`) inside the container whose User ID (UID) and Group ID (GID) exactly match the host user running the container.
*   **Implementation:** Use build arguments (`ARG USER_ID`, `ARG GROUP_ID`) in the `Dockerfile` to create this user dynamically.

### 4. ddtFoam Integration
*   **Source Code:** The local `ddtfoam-code` directory will be copied into the container during the build phase to the `$WM_PROJECT_USER_DIR`.
*   **Compilation:** The solver will be compiled using OpenFOAM's `wmake` command within the `Dockerfile` so that the resulting image is ready to use immediately.

### 5. Orchestration (Docker Compose)
*   **Service Definition:** A single service (`openfoam`) in `docker-compose.yml`.
*   **Volumes:** Bind mount the local `./docker_root` directory to `/home/openfoam/project` inside the container.
*   **Environment Variables:** Pass local user UID and GID to the build process.

## Data Flow
1.  **Build Phase:** Docker downloads Ubuntu 14.04, installs OpenFOAM 2.1.1, creates the user, copies `ddtfoam-code`, and compiles it.
2.  **Runtime:** The user runs `docker compose run --rm openfoam`. The container starts, mounts `./docker_root`, logs in as the mapped user, and drops into a bash shell with OpenFOAM sourced and ready.

## Trade-offs
*   **Security of Ubuntu 14.04:** It is End-of-Life (EOL), but acceptable for an isolated, local computational container that does not expose external web services.
*   **Image Size:** A single-stage build will be larger than a multi-stage one (as it retains build tools), but it is much simpler to debug and guarantees library compatibility for the legacy solver.
