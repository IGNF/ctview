
install:
	mamba env update -n ctview -f environment.yml

install-precommit:
	pre-commit install