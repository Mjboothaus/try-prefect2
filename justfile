# Docs: https://just.systems/man/en/

project_name := "try-prefect2"
# app_py := "src/Main.py"
server_port := "UNDEFINED"
gcp_region := "asia-southeast2"

set dotenv-load

# show available commands
help:
  @just -l


docs:
	open https://docs.prefect.io/tutorials/first-steps/
	open https://orion-docs.prefect.io/getting-started/overview/
	open https://orion-docs.prefect.io/concepts/overview/


start-agent tag_name:
	prefect agent start --tag {{tag_name}}
	# e.g. tag = macbook_air_m1_2020
	# https://docs.prefect.io/concepts/work-queues/#agent-configuration


start-ui:
	prefect orion start


open-ui:
	open http://127.0.0.1:4200


port-process port:
	sudo lsof -i :{{port}}


version: (activate "dev")
	prefect --version


# Create the local Python venv (.venv_{{project_name}}) and install requirements(.txt)

venv dev_deploy:
	#!/usr/bin/env bash
	pip-compile requirements-{{dev_deploy}}.in
	python3 -m venv .venv_{{dev_deploy}}_{{project_name}}
	. .venv_{{dev_deploy}}_{{project_name}}/bin/activate
	python3 -m pip install --upgrade pip
	pip install -r requirements-{{dev_deploy}}.txt
	python -m ipykernel install --user --name .venv_{{dev_deploy}}_{{project_name}}
	pip install -U prefect
	echo -e '\n' source .venv_{{dev_deploy}}_{{project_name}}/bin/activate '\n'


activate dev_deploy:
	#!/usr/bin/env zsh
	echo -e '\n' source .venv_{{dev_deploy}}_{{project_name}}/bin/activate '\n'


update-dev-reqs:
	pip-compile requirements-dev.in
	pip install -r requirements-dev.txt --upgrade


update-deploy-reqs:
	pip-compile requirements-deploy.in
	pip install -r requirements-deploy.txt --upgrade

# See custom dvenv command defined in ~/.zshrc

rm-dev-venv:
	#!/usr/bin/env bash
	dvenv
	rm -rf .venv_dev_{{project_name}}


rm-deploy-venv:
	#!/usr/bin/env bash
	dvenv
	rm -rf .venv_deploy_{{project_name}}

test:
    pytest


run-job-local:
	#!/usr/bin/env bash
	start=`date +%s`
	python src/beach_swim_daily_job.py
	end=`date +%s`
	runtime=$((end-start))
	echo ""
	echo $runtime seconds to run job
	echo ""

# Run notebook locally

run: 
	#!/usr/bin/env bash
	echo "Need to setup for non-app i.e. Prefect-friendly"    

# streamlit run {{app_py}} --server.port={{server_port}} --server.address=localhost

# Build and run app.py in a (local) Docker container

container: 
    docker build . -t {{project_name}}
    docker run -p {{server_port}}:{{server_port}} {{project_name}}


# Still in progress - still not STP
gcr-setup:
    gcloud components update
    # gcloud config set region asia-southeast2
    gcloud projects create {{project_name}}
    gcloud beta billing projects link {{project_name}} --billing-account $BILLING_ACCOUNT_GCP
    gcloud services enable cloudbuild.googleapis.com
    gcloud config set project {{project_name}}


# Deploy container to Google Cloud (Cloud Run)

gcr-deploy: 
    gcloud run deploy --source . {{project_name}} --region {{gcp_region}}


gcr-list-deployed-url:
    gcloud run services list --platform managed | awk 'NR==2 {print $4}'


gcr-app-disable:   # deleting project does not delete app
    gcloud app versions list


#TODO: 
# gloud init - other stuff?
# gcloud projects list


# Resources:
# - https://stackoverflow.com/questions/59423245/how-to-get-or-generate-deploy-url-for-google-cloud-run-services