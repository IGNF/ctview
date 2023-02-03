FROM continuumio/miniconda3 AS build

RUN git clone http://gitlab.forge-idi.ign.fr/Lidar/ctView.git

WORKDIR /ctView

RUN conda env create -n ctview -f environment.yml

ENTRYPOINT ["conda", "run", "-n", "ctview"]
