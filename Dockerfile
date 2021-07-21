FROM tensorflow/tensorflow:1.15.4-gpu-py3

LABEL name=deeplesionbrain \
      version=0.1 \
      maintainer=reda-abdellah.kamraoui@labri.fr \
      net.volbrain.pipeline.mode=gpu_only \
      net.volbrain.pipeline.name=assemblyNet


RUN curl -LO http://ssd.mathworks.com/supportfiles/downloads/R2017b/deployment_files/R2017b/installers/glnxa64/MCR_R2017b_glnxa64_installer.zip && \
    mkdir MCR && \
    cp MCR_R2017b_glnxa64_installer.zip MCR && \
    cd MCR && \
    unzip MCR_R2017b_glnxa64_installer.zip && \
    ./install -mode silent -agreeToLicense yes && \
    cd .. && \
    rm -rf MCR

# required to be able to do "apt update", that is necessary to install texlive-xetex
ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NONINTERACTIVE_SEEN=true


WORKDIR /opt/deeplesionbrain

ENV LD_LIBRARY_PATH=/usr/local/MATLAB/MATLAB_Runtime/v93/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v93/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v93/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v93/sys/opengl/lib/glnxa64:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
ENV XAPPLRESDIR=/usr/local/MATLAB/MATLAB_Runtime/v93/X11/app-defaults
ENV MCR_CACHE_VERBOSE=true
ENV MCR_CACHE_ROOT=/tmp

RUN mkdir /usr/local/MATLAB/MATLAB_Runtime/v93/sys/os/glnxa64/exclude
RUN mkdir /usr/local/MATLAB/MATLAB_Runtime/v93/bin/glnxa64/exclude
RUN mv /usr/local/MATLAB/MATLAB_Runtime/v93/sys/os/glnxa64/libstdc++.so.6.* /usr/local/MATLAB/MATLAB_Runtime/v93/sys/os/glnxa64/exclude/
RUN mv /usr/local/MATLAB/MATLAB_Runtime/v93/bin/glnxa64/libfreetype* /usr/local/MATLAB/MATLAB_Runtime/v93/bin/glnxa64/exclude/

RUN echo deb http://archive.ubuntu.com/ubuntu/ trusty main restricted universe multiverse  >> /etc/apt/sources.list
RUN echo deb http://archive.ubuntu.com/ubuntu/ trusty-security main restricted universe multiverse  >> /etc/apt/sources.list
RUN echo deb http://archive.ubuntu.com/ubuntu/ trusty-updates main restricted universe multiverse  >> /etc/apt/sources.list
RUN echo deb http://archive.ubuntu.com/ubuntu/ trusty-proposed main restricted universe multiverse  >> /etc/apt/sources.list
RUN echo deb http://archive.ubuntu.com/ubuntu/ trusty-backports main restricted universe multiverse  >> /etc/apt/sources.list
RUN apt-get update
RUN apt -qqy install libx11-dev xserver-xorg libfontconfig1 libxt6 libxcomposite1 libasound2 libxext6 texlive-xetex

RUN wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=13pZYD3ZS89SfDWsakIbZGV5Bgyen2qv7' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=13pZYD3ZS89SfDWsakIbZGV5Bgyen2qv7" -O Compilation_lesionBrain_v10.zip && rm -rf /tmp/cookies.txt
RUN unzip Compilation_lesionBrain_v10.zip
RUN cp -avr Compilation_lesionBrain_v10 /opt/deeplesionbrain

RUN pip3 install scikit-learn statsmodels  keras==2.2.4 pillow nibabel==2.5.2 scikit-image==0.17.2
RUN mkdir /Weights
#COPY trained_all_second_step_iqda/* /Weights/
RUN wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1XgcUEek_sILlCJMzuIR-7Ti0nHHJLwdN' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1XgcUEek_sILlCJMzuIR-7Ti0nHHJLwdN" -O trained_all_second_step_iqda.zip && rm -rf /tmp/cookies.txt
RUN unzip trained_all_second_step_iqda.zip
RUN cp -avr trained_all_second_step_iqda/* /Weights/

RUN ls /Weights/
RUN git clone https://github.com/Reda-Abdellah/DLB_docker.git
RUN cp -avr DLB_docker /opt/deeplesionbrain

RUN mkdir /data/
