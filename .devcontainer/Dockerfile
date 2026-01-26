FROM debian:12

RUN apt-get update &&\
    apt-get install -y build-essential curl locales git hunspell \
        imagemagick python3 python3-pip python3-venv texlive-full &&\
    localedef -i en_CA -c -f UTF-8 -A /usr/share/locale/locale.alias \
        en_CA.UTF-8 &&\
    apt-get clean

ENV LANG=en_CA.utf8

COPY install_sage_kernel.py /tmp/

SHELL ["/bin/bash", "-c"]

RUN curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" &&\
    bash Miniforge3-$(uname)-$(uname -m).sh -b &&\
    source /root/miniforge3/bin/activate &&\
    conda init bash

SHELL ["/root/miniforge3/bin/conda", "run", "--live-stream", "/bin/bash", "-c"]

RUN conda create -n sage sage python=3.11 pytest sphinx furo

SHELL ["/root/miniforge3/bin/conda", "run", "--live-stream", "-n", "sage", "/bin/bash", "-c"]

RUN python3 /tmp/install_sage_kernel.py &&\
    echo "conda activate sage" >> ~/.bashrc