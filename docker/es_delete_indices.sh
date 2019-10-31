#!/usr/bin/env sh

set -e

echo "Delete existing ES indices"
docker-compose exec -T web python manage.py search_index --delete
