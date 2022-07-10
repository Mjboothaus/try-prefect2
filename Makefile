pip-compile:
	pip-compile requirements.in && pip-compile --upgrade-package 'prefect>=2.0b'

venv-reqs:
	python3 -m pip install --upgrade pip && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt 

install-jupyter-kernel:
	python -m ipykernel install --user --name=.venv