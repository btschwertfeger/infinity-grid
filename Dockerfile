FROM python:3.13-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /apps
COPY . /apps

# hadolint ignore=DL3013,DL3008
RUN --mount=type=cache,target=/var/lib/apt/,sharing=locked \
--mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=tmpfs,target=/var/log/apt/ \
    apt-get update \
    && apt-get install --no-install-recommends -y git

# hadolint ignore=DL3013
RUN python -m pip install --no-cache-dir --compile --upgrade pip build \
    && python -m build .

# ------------------------------------------------------------------------------

FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /home/infinity-grid

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
        gcc \
        libpq-dev \
        locales \
        procps \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# hadolint ignore=SC2102,DL3013
RUN --mount=type=bind,target=/context,from=builder,source=/apps \
    python -m pip install --compile --no-cache-dir $(find /context/dist -name "*.whl")[kraken]

USER infinity-grid

EXPOSE 8080

ENTRYPOINT ["infinity-grid", "run"]

LABEL title="Infinity Grid"
LABEL maintainer="Benjamin Thomas Schwertfeger contact@b-schwertfeger.de"
LABEL description="The Infinity Grid Trading Algorithm."
LABEL documentation="https://infinity-grid.readthedocs.io/en/stable"
LABEL image.url="https://github.com/btschwerfeger/infinity-grid"
