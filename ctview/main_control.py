import hydra
from omegaconf import DictConfig
from osgeo import gdal

from ctview.main_ctview import main_ctview


@hydra.main(config_path="../configs/", config_name="config_control.yaml", version_base="1.2")
def main(config: DictConfig):
    main_ctview(config)


if __name__ == "__main__":
    gdal.UseExceptions()
    main()
