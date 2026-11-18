#!/usr/bin/env bash
# starts Rihla on Linux or macOS: the server in the background, then the app
# needs PostgreSQL running with the rihla database (see README)
cd "$(dirname "$0")"

python3 server/server.py &
SERVER=$!
# stop the server when the app closes
trap "kill $SERVER" EXIT

sleep 2
cd desktop && npx electron .
