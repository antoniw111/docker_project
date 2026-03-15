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
