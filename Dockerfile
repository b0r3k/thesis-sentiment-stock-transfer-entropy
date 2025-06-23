FROM python:3.12-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    cmake \
    libopenmpi-dev \
    opencl-headers \
    ocl-icd-opencl-dev \
    default-jdk \
    clinfo

# Set up the OpenCL nvidia environment
ENV NVIDIA_VISIBLE_DEVICES="all"
ENV NVIDIA_DRIVER_CAPABILITIES="compute,utility"
ENV PYOPENCL_COMPILER_OUTPUT=1

RUN mkdir -p /etc/OpenCL/vendors && \
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

# Set up venv and IDTxl
ENV VENV=/opt/.venv
ENV IDTXL=/opt/IDTxl

RUN python -m venv $VENV && \
$VENV/bin/pip install --no-cache-dir --upgrade \
    pip \
    setuptools==80.9.0 \
    wheel==0.45.1 \
    matplotlib==3.10.3 \
    pandas==2.3.0 \
    statsmodels==0.14.4 \
    h5py==3.14.0 \
    networkx==3.5 \
    jpype1==1.5.2 \
    pyopencl==2025.2.4

# Clone and install IDTxl from a specific commit
RUN git clone "https://github.com/pwollstadt/IDTxl.git" $IDTXL && \
cd $IDTXL && \
git checkout "d78480d14d6e7c62597e0935d9ce7d6cc2238611" && \
$VENV/bin/pip install --no-cache-dir -e .

# Fix a bug in IDTxl with new numpy versions
RUN sed -i '4i import math' $IDTXL/idtxl/stats.py && \
    sed -i 's/np\.math\.factorial/math.factorial/g' $IDTXL/idtxl/stats.py

WORKDIR /opt
