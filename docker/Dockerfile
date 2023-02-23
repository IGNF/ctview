FROM continuumio/miniconda3 AS build

RUN git clone http://gitlab.forge-idi.ign.fr/Lidar/ctView.git

WORKDIR /ctView

RUN conda env create -n ctview -f environment.yml

SHELL ["conda", "run", "-n", "ctview", "/bin/bash", "-c"]

RUN python -c "import pdal"

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "ctview"]
