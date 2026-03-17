# Use a loacal rm314159/openfoam211 copy
FROM openfoam211
#FROM rm31415/openfoqm211
USER root

# Install build dependencies missing in the base image
RUN apt-get update && apt-get install -y \
    build-essential \
    flex \
    bison \
    zlib1g-dev \
    openssh-client \
    openssh-server \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Build arguments for user mapping
ARG USER_ID
ARG GROUP_ID
ARG USER_NAME=openfoam

# Create a non-root user with the same UID/GID as the host user
RUN groupadd -g ${GROUP_ID} ${USER_NAME} || true && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -m -s /bin/bash ${USER_NAME} || true

# Set up the OpenFOAM environment for the user
RUN echo "source /opt/openfoam211/etc/bashrc" >> /home/${USER_NAME}/.bashrc

# Define the user directory for OpenFOAM
ENV WM_PROJECT_USER_DIR=/home/${USER_NAME}/OpenFOAM/${USER_NAME}-2.1.1
RUN mkdir -p ${WM_PROJECT_USER_DIR} && chown -R ${USER_NAME}:${GROUP_ID} /home/${USER_NAME}/OpenFOAM

# Switch to the new user
USER ${USER_NAME}
WORKDIR /home/${USER_NAME}

# Copy the ddtfoam-code into the container
RUN /bin/bash -c "cd ${WM_PROJECT_USER_DIR} && git clone https://github.com/antoniw111/ddtFoam.git"

# Compile ddtFoam
# We source the global bashrc and run Allwmake
RUN /bin/bash -c "source /opt/openfoam211/etc/bashrc && cd ${WM_PROJECT_USER_DIR}/ddtFoam && ./Allwmake"

# Default command: open a bash shell
CMD ["/bin/bash"]
