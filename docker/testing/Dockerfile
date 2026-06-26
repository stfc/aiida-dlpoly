FROM ubuntu:24.04 

LABEL maintainer="Dr. Benjamin T. Speake <benjamin.speake@stfc.ac.uk>"

USER root 
SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive \
    SHELL=/bin/bash 

RUN apt update -y && apt upgrade -y && \
    apt install --yes --no-install-recommends \
    build-essential cmake git ca-certificates gfortran \
    wget bzip2 && \
    apt clean --yes && rm -rf /var/lib/apt/lists/* 

ENV CONDA_DIR=/opt/conda 
ENV PATH="${CONDA_DIR}/bin:${PATH}"
WORKDIR /tmp 
RUN set -x && \ 
    wget -qO- "https://micro.mamba.pm/api/micromamba/linux-64/latest" | tar -xvj bin/micromamba && \
    ./bin/micromamba install --root-prefix="${CONDA_DIR}" --prefix="${CONDA_DIR}" --yes \
    "python=3.12" "pyscf" "aiida-core" "mamba" "conda" "pytest" "pytest-cov"  && \ 
    rm -rf /tmp/bin/ && \ 
    mamba clean --all -f -y 

WORKDIR /opt/
RUN git clone https://gitlab.com/ccp5/dl-poly.git && \
    mkdir dlpoly && cd dlpoly && \
    FC=gfortran cmake ../dl-poly -DBUILDER="Dr. Benjamin T. Speake" -DWITH_MPI=OFF && \
    make -j 4 && \
    rm -rf /opt/dl-poly

ENV DLPOLY_BIN=/opt/dlpoly/bin/DLPOLY.Z

WORKDIR /opt/
