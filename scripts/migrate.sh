#!/usr/bin/env bash

set -e
set -x

# Run the one-shot prestart job to apply migrations and seed initial data
docker compose run --rm prestart


