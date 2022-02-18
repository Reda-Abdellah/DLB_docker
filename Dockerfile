FROM nvcr.io/nvidia/tensorflow:21.08-tf1-py3
#FROM tensorflow/tensorflow:1.15.4-gpu-py3

LABEL name=deeplesionbrain \
      version=1.0 \
      maintainer=reda-abdellah.kamraoui@labri.fr \
      net.volbrain.pipeline.mode=gpu_only \
      net.volbrain.pipeline.name=assemblyNet

RUN curl -LO https://ssd.mathworks.com/supportfiles/downloads/R2017b/deployment_files/R2017b/installers/glnxa64/MCR_R2017b_glnxa64_installer.zip && \
    mkdir MCR && \
    cp MCR_R2017b_glnxa64_installer.zip MCR && \
    cd MCR && \
    unzip MCR_R2017b_glnxa64_installer.zip && \
    ./install -mode silent -agreeToLicense yes && \
    cd .. && \
    rm -rf MCR

ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NONINTERACTIVE_SEEN=true
RUN mkdir -p /opt/deeplesionbrain
WORKDIR /opt/deeplesionbrain

RUN apt-get update
# RUN apt -qqy install libx11-dev xserver-xorg libfontconfig1 libxt6 libxcomposite1 libasound2 libxext6 texlive-xetex
RUN apt -qqy install libfontconfig1 libxt6 libxext6 texlive-xetex

COPY MATLAB/Compilation_lesionBrain_v11_fullpreprocessing/ /opt/deeplesionbrain/
RUN chmod +x /opt/deeplesionbrain/lesionBrain_v11_fullpreprocessing_exe
RUN chmod +x /opt/deeplesionbrain/lesionBrain_v11_fullpreprocessing_exe.sh
RUN chmod +x /opt/deeplesionbrain/IHCorrection/CompilationSPM8/spm8

RUN pip3 install statsmodels  keras==2.2.4 pillow nibabel==2.5.2 scikit-image==0.17.2 pandas

RUN mkdir /Weights
COPY trained_all_second_step_iqda/ /Weights/

COPY end_to_end_pipeline_file.py end_to_end_pipeline.py make_reports.py modelos.py prediction.py preprocessing.py report_utils.py utils.py header.png female_vb_bounds.pkl male_vb_bounds.pkl average_vb_bounds.pkl README.pdf /opt/deeplesionbrain/

#RUN mkdir /data/

# RUN mv /usr/local/MATLAB/MATLAB_Runtime/v93/bin/glnxa64/libmwcoder_types.so* /usr/local/MATLAB/MATLAB_Runtime/v93/sys/os/glnxa64/exclude/
RUN apt -qqy install libatk1.0-0

ENTRYPOINT [ "python3", "/opt/deeplesionbrain/end_to_end_pipeline_file.py" ]
