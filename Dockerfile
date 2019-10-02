# `docs_italia_it_base`: Base Image
# Image used as a common base for the multi stage process
# Not really used by any container

FROM python:3.6-slim AS docs_italia_it_base

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        libpq-dev \
        libxslt1-dev \
        unzip \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && apt-get clean

ENV APPDIR /app
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1 DEBUG=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# `docs_italia_it_test`: Test Image
# Used in `docker-compose-test`.
# As all the test will run in a tox virtualenv we need development libraries here
# We don't need code in this image as will be mounted the live one via the local
# volume

FROM docs_italia_it_base AS docs_italia_it_test

RUN pip install --no-cache-dir tox

CMD ["/bin/bash"]
# `docs_italia_it_build`: Stage for celery-build
# We need additional packages to build documentation in LocalBuildEnvironment

FROM docs_italia_it_base AS docs_italia_it_build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libfreetype6-dev \
        libjpeg-dev \
        libjpeg-turbo-progs \
        libtiff5-dev \
        curl \
        doxygen \
        libcairo2-dev \
        libenchant1c2a \
        libevent-dev \
        libgraphviz-dev \
        liblcms2-dev \
        libwebp-dev \
        pandoc \
        pkg-config \
        python-m2crypto \
        python-matplotlib \
        python-pip \
        python-virtualenv \
        python2.7 \
        python2.7-dev \
        sqlite \
        texlive-extra-utils \
        texlive-fonts-recommended \
        texlive-generic-recommended \
        texlive-latex-extra \
        texlive-latex-recommended \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && apt-get clean

COPY _build/converter/converti _build/converter/pandoc* _build/converter/filtro* /usr/local/bin/
RUN chmod 755 /usr/local/bin/converti /usr/local/bin/pandoc* /usr/local/bin/filtro-*

CMD ["/bin/bash"]

# `docs_italia_it_dev`: Application Image
# Image for all the application containers
# We don't need to copy the RTD code in this image as will be mounted the live
# one via the local volume. We only need to copy the files needed inside the
# container (utility shell scripts and requirements)

FROM docs_italia_it_build AS docs_italia_it_dev

RUN python -mvenv /virtualenv
COPY requirements/ /app/requirements/
COPY docker/ /app/docker/
RUN /virtualenv/bin/pip install -r /app/requirements/docsitalia-converter.txt
ENV DJANGO_SETTINGS_MODULE=readthedocs.docsitalia.settings.docker

CMD ["/bin/bash"]

FROM docs_italia_it_dev AS docs_italia_it_prod

COPY readthedocs/ /app/readthedocs/
COPY media/ /app/media/
COPY manage.py /app

CMD ["/bin/bash"]
