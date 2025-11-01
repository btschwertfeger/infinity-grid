# -*- mode: dockerfile; coding: utf-8 -*-
#
# Copyright (C) 2023 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#

FROM python:3.14-slim-bookworm

ARG EXTRAS="kraken"
ARG VERSION
ARG CREATE_TIME

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /home/infinity-grid

EXPOSE 8080

RUN groupadd -r infinity-grid \
    && useradd -r -g infinity-grid -d /home/infinity-grid -s /bin/bash -c "Infinity Grid User" infinity-grid \
    && mkdir -p /home/infinity-grid \
    && chown -R infinity-grid:infinity-grid /home/infinity-grid

# hadolint ignore=DL3008
RUN --mount=type=cache,target=/var/lib/apt/,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=tmpfs,target=/var/log/apt/ \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo "LC_ALL=en_US.UTF-8" >> /etc/environment \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "LANG=en_US.UTF-8" >> /etc/locale.conf \
    && apt-get update \
    && apt-get -y upgrade \
    && apt-get -y --no-install-recommends install \
        curl \
        gcc \
        libpq-dev \
        locales \
        procps \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# hadolint ignore=SC2046,DL3013,DL3042
RUN --mount=type=bind,target=/context,source=/dist \
    --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    python -m pip install --compile $(find /context -name "*.whl")["${EXTRAS}"]

USER infinity-grid

ENTRYPOINT ["infinity-grid", "run"]

LABEL org.opencontainers.image.description="The Infinity Grid Trading Algorithm."
LABEL org.opencontainers.image.documentation="https://infinity-grid.readthedocs.io/en/stable"
LABEL org.opencontainers.image.authors="Benjamin Thomas Schwertfeger contact@b-schwertfeger.de"
LABEL org.opencontainers.image.source="https://github.com/btschwerfeger/infinity-grid"
LABEL org.opencontainers.image.license="LicenseRef-Infinity-Grid-2.0"
LABEL org.opencontainers.image.title="Infinity Grid"
LABEL org.opencontainers.image.version=${VERSION}
LABEL org.opencontainers.image.created=${CREATE_TIME}
