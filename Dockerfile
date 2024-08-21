FROM mambaorg/micromamba:latest

USER root
# Remove any third-party apt sources to avoid issues with expiring keys
RUN rm -f /etc/apt/sources.list.d/*.list
# install required libs
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ctView

# # Set up the Conda environment: cf https://github.com/mamba-org/micromamba-docker
COPY environment.yml /tmp/env.yaml
COPY requirements.txt /tmp/requirements.txt
RUN chown $MAMBA_USER:$MAMBA_USER /tmp/env.yaml
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

ENV ENV_NAME base
ARG MAMBA_DOCKERFILE_ACTIVATE=1

COPY ctview ctview
COPY data data
COPY configs configs
COPY test test

RUN mkdir tmp
