# Sandbox image for the LAB-Bench code-tools tasks.
# Provides the biology package set; the model may install more at run time.

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
        biopython==1.85 \
        pydna==5.5.0 \
        primer3-py==2.2.0 \
        pandas==2.2.3 \
        numpy==2.2.1

WORKDIR /workspace
