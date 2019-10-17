#!/usr/bin/env sh

set -e

docker/dirs.sh
if [ "$1" = "collect" ]; then
  cp -a media /home/documents/
  /virtualenv/bin/python manage.py collectstatic --no-input -c
  /virtualenv/bin/python manage.py migrate
  /virtualenv/bin/python manage.py reindex_elasticsearch
fi
sleep 10
/virtualenv/bin/gunicorn --error-logfile="-" --timeout=3000  readthedocs.wsgi:application $*
