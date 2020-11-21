#!/bin/bash

cd "$(dirname "$0")"

sudo certbot --config-dir=config --work-dir=work --logs-dir=logs certonly --standalone -d home.lunderberg.com
sudo chown -R $(whoami) *
