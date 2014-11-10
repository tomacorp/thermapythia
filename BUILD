#!/bin/sh
# Tom Anderson
# Fri Jul 18 08:13:16 PDT 2014
# Fri Jul 25 00:56:29 PDT 2014
# See also:
# https://software.sandia.gov/pipermail/trilinos-users/
#
# First built openmpi, pcre, swig, hdf5
# complains maximum swig version is 2.0.8
# Fixed it by installing 2.0.8

PATH=/Users/toma/python278i/bin
PATH=$PATH:/Applications/CMake.app/Contents/bin
PATH=$PATH:/usr/bin
PATH=$PATH:/bin
PATH=$PATH:/usr/local/bin
PATH=$PATH:/opt/X11/bin
PATH=$PATH:/usr/sbin
PATH=$PATH:/sbin
PATH=$PATH:/Users/toma/perl/bin
PATH=$PATH:/Users/toma/tools/bin
PATH=$PATH:/Users/toma/bin
PATH=$PATH:/Users/toma/tools/trilinos
export PATH

export WORKDIR=/Users/toma/tools

export CC=clang
export CXX=clang
export FFLAGS=-ff2c
export BUILD=$WORKDIR/trilinos-build
export SOURCE=$WORKDIR/trilinos-11.8.1-Source
export SOURCE_DIST=/Users/toma/Downloads/trilinos-11.8.1-Source.tar.gz

# Trilinos build
# Potential problem: make sure it does not use pylib from 2.7.5 from /usr/lib instead of the 2.7.8 build in /Users/toma/...
rm -rf $SOURCE
cd $WORKDIR
tar -zxf $SOURCE_DIST

rm -rf $BUILD
mkdir $BUILD
cd $BUILD

cmake \
-D CMAKE_C_COMPILER=/usr/bin/clang \
-D CMAKE_CXX_COMPILER=/usr/bin/clang++ \
-D Trilinos_ENABLE_Fortran:BOOL=OFF \
-D Trilinos_ENABLE_ALL_PACKAGES:BOOL=ON \
-D TPL_ENABLE_MPI:BOOL=OFF \
-D Trilinos_ENABLE_PyTrilinos:BOOL=ON \
-D TPL_ENABLE_HDF5:STRING=ON \
-D EpetraExt_USING_HDF5:BOOL=ON \
-D HDF5_LIBRARY_NAMES:STRING="hdf5" \
-D HDF5_LIBRARY_DIRS:FILEPATH=/Users/toma/tools/hdf5/lib \
-D TPL_HDF5_INCLUDE_DIRS:FILEPATH=Users/toma/tools/hdf5/include \
-D BUILD_SHARED_LIBS:BOOL=ON \
-D CMAKE_INSTALL_PATH=$WORKDIR/trilinos \
$SOURCE

make -j2
# sudo make install

# HDF5 instructions from: https://github.com/CamelliaDPG/Camellia
# //Enable EpetraExt interface support for HDF5. This interface requires
# // an already installed HDF5 library\; the include, the library
# // path and the library name must be specified as well.
# -D EpetraExt_USING_HDF5:BOOL=ON
# -D HDF5_LIBRARY_DIRS:FILEPATH=/usr/local/lib \
# -D HDF5_LIBRARY_NAMES:STRING="hdf5" \
# -D TPL_HDF5_INCLUDE_DIRS:FILEPATH=/usr/local/include \
#
# There is also an XML reader that would be good to have.

# Build takes a long time. Can use make -j2
# real	68m35.863s
# user	56m52.859s
# sys	5m54.863s


