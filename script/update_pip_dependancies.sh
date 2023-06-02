#!/bin/bash
source script/get_conda.sh
conda activate ctview

# re install pip dependancies, force the download of the libs, with our private repo (Nexus).
pip install -U --force-reinstall -r requirements.txt --extra-index-url=https://nexus.ign.fr/repository/pypi-lidarhd-hosted/simple
