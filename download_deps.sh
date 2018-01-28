#!/bin/bash

cd $(dirname "${BASH_SOURCE[0]}")

mkdir -p web-serve/deps
cd web-serve/deps

wget -O plotly-latest.min.js https://cdn.plot.ly/plotly-latest.min.js
