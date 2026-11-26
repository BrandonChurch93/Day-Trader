#!/bin/bash
# Pinned TM09 engine launcher, run as the service account through the timed operator sudo wrapper with plain
# arguments only, so its sudo log line matches the operator record exactly. usage: tm09_engine.sh COMMAND ARGS...
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
exec env -i PATH=/usr/bin:/bin PYTHONNOUSERSITE=1 nice -n 10 /usr/bin/python3.14 -B -m timemachine.tm09_operator "$@"
