#!/usr/bin/env bash

set -e

export COMANDI_CONVERSIONE_VERSION=v0.6
export PANDOC_FILTERS_VERSION=v0.1.4


mkdir -p _build/converter

cd _build/converter
wget -nc -q https://github.com/italia/docs-italia-comandi-conversione/releases/download/${COMANDI_CONVERSIONE_VERSION}/converti.zip
wget -nc -q https://github.com/italia/docs-italia-comandi-conversione/releases/download/${COMANDI_CONVERSIONE_VERSION}/pandoc-font-to-style.zip
wget -nc -q https://github.com/italia/docs-italia-comandi-conversione/releases/download/${COMANDI_CONVERSIONE_VERSION}/pandoc-to-sphinx.zip
wget -nc -q https://github.com/italia/docs-italia-comandi-conversione/releases/download/${COMANDI_CONVERSIONE_VERSION}/pandoc.zip
wget -nc -q https://github.com/italia/docs-italia-pandoc-filters/releases/download/${PANDOC_FILTERS_VERSION}/filtro-acronimi
wget -nc -q https://github.com/italia/docs-italia-pandoc-filters/releases/download/${PANDOC_FILTERS_VERSION}/filtro-didascalia
wget -nc -q https://github.com/italia/docs-italia-pandoc-filters/releases/download/${PANDOC_FILTERS_VERSION}/filtro-google-docs
wget -nc -q https://github.com/italia/docs-italia-pandoc-filters/releases/download/${PANDOC_FILTERS_VERSION}/filtro-quotes
wget -nc -q https://github.com/italia/docs-italia-pandoc-filters/releases/download/${PANDOC_FILTERS_VERSION}/filtro-references
wget -nc -q https://github.com/italia/docs-italia-pandoc-filters/releases/download/${PANDOC_FILTERS_VERSION}/filtro-rimuovi-div
wget -nc -q https://github.com/italia/docs-italia-pandoc-filters/releases/download/${PANDOC_FILTERS_VERSION}/filtro-stile-liste

unzip -oqq '*.zip'
chmod +x converti* pandoc* filtro*
