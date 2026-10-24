# GalSpec full-continuum + emission-line model
# Build context is the repository root:
#   docker build -f Tools/galspec_line/dockerfile -t galspec_line .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      git ca-certificates gcc g++ libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY Tools/galspec_line/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Pinned upstream commit.  The package is installed from the public repository;
# no GalSpec source or example data is vendored into this repository.
ARG GALSPEC_COMMIT=18e4effd796a1d51615ca2340bb927278eb18bbf
ENV GALSPEC_COMMIT=${GALSPEC_COMMIT}
RUN pip install --no-cache-dir --no-deps \
      "galspec @ git+https://github.com/jyshangguan/GalSpec.git@${GALSPEC_COMMIT}"

COPY Tools/galspec_line/run_galspec.py /app/galspec_line/run_galspec.py
COPY Tools/galspec_line/galspec_full.py /app/galspec_line/galspec_full.py
COPY configs/galspec_line /app/config

RUN mkdir -p /app/input /app/output && chmod 777 /app/output

LABEL org.opencontainers.image.title="galspec_line" \
      org.opencontainers.image.description="GalSpec full-continuum QSO emission-line fit with emcee" \
      org.opencontainers.image.source="https://github.com/jyshangguan/GalSpec" \
      org.opencontainers.image.revision="18e4effd796a1d51615ca2340bb927278eb18bbf"

ENTRYPOINT ["python", "/app/galspec_line/run_galspec.py"]
