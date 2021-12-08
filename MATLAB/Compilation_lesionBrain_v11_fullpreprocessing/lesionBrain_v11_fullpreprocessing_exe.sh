#!/bin/sh

LD_LIBRARY_PATH_BAK=$LD_LIBRARY_PATH

LD_LIBRARY_PATH=/usr/local/MATLAB/MATLAB_Runtime/v93/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v93/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v93/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v93/sys/opengl/lib/glnxa64:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
XAPPLRESDIR=/usr/local/MATLAB/MATLAB_Runtime/v93/X11/app-defaults
MCR_CACHE_VERBOSE=true
MCR_CACHE_ROOT=/tmp

export LD_LIBRARY_PATH

if [ $# != 2 ]
then
   echo "ERROR: wrong number of arguments"
   echo "Usage: $0 <input_T1_filename> <input_FLAIR_filename>"
   exit 1
fi

#necessary when using nvcr.io/nvidia/tensorflow:21.08-tf1-py3
rm -f /usr/local/MATLAB/MATLAB_Runtime/v93/bin/glnxa64/libfreetype.so.6 /usr/local/MATLAB/MATLAB_Runtime/v93/sys/os/glnxa64/libstdc++.so.6.* /usr/local/MATLAB/MATLAB_Runtime/v93/bin/glnxa64/libmwcoder_types.so*

./lesionBrain_v11_fullpreprocessing_exe "$1" "$2"

LD_LIBRARY_PATH=$LD_LIBRARY_PATH_BAK

export LD_LIBRARY_PATH

