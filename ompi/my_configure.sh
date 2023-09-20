#!/bin/bash

# Enable undefined variable detection
set -u

# Check if the variable exists
if [ ! -v MPI_HOME ]; then
    echo "Error: Variable MPI_HOME does not exist"
    exit 1  # Terminate the program and return error code 1
fi
echo "MPI_HOME: $MPI_HOME"

if [ ! -v V_UCX_HOME ]; then
    echo "Error: Variable V_UCX_HOME does not exist"
    exit 1  # Terminate the program and return error code 1
fi
echo ""
echo "V_UCX_HOME: $V_UCX_HOME"

echo ""
echo "Configure with:"
echo "--prefix=$MPI_HOME --with-ucx=$V_UCX_HOME --enable-mca-no-build=btl-uct"
echo "FC=/usr/bin/gfortran CC=/usr/bin/gcc CXX=/usr/bin/c++"
echo "--with-ucx-libdir=${V_UCX_HOME}/lib"
echo "LDFLAGS=-L${V_UCX_HOME}/lib"

./configure --prefix=$MPI_HOME --with-ucx=$V_UCX_HOME --enable-mca-no-build=btl-uct \
FC=/usr/bin/gfortran CC=/usr/bin/gcc CXX=/usr/bin/c++ \
--with-ucx-libdir=${V_UCX_HOME}/lib \
LDFLAGS=-L${V_UCX_HOME}/lib

# Use my_variable here
echo ""
echo "Completed."