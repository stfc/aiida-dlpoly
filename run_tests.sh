#!/bin/bash

PYTEST_CMD='cd /opt/aiida-dlpoly && pip install . && pytest --cov=aiida_dlpoly --cov-report=xml:/opt/aiida-dlpoly/coverage.xml'  
IMAGE_NAME=ghcr.io/stfc/aiida-dlpoly/testing:latest
docker run --rm -v $(pwd):/opt/aiida-dlpoly $IMAGE_NAME bash -c "$PYTEST_CMD"
