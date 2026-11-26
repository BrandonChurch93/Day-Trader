#!/bin/bash
# TM09 copy of the TM07 review step (review.sh): stop, stopped probe, cut the sudo lines since the checkpoint,
# match them to the operator records, sign the review boundary only if nothing is unlisted, engine review.
# usage: tm09_review.sh MODE "ROLE_ARGS" SESSION PORT NONCE SIBLING BEARER_FILE   (same env as tm09_launch.sh)
set -euo pipefail
. "$(dirname "$0")/tm09_ops_env.sh"
setup "$@"
[ $# = 7 ] || usage
NONCE=$5; SIB=$6; BEARER=$7
[[ $NONCE =~ ^[0-9a-f]{32}$ ]] || usage
bearer_file "$BEARER"
stop_listener
ops probe stopped "$SESSION" "$PORT" "$NONCE" "$SIB" "$BEARER"
ops entries "$SESSION" "$PORT" "$NONCE"
mkdir -p -m 700 "$LOGS"; W=$LOGS/review-$SESSION-$NONCE; mkdir -m 700 "$W"
"$OSUDO" cat "$CONTROL/$SESSION-$NONCE.entries.json" > "$W/entries.json"
ops canaries > "$W/canaries.json"
python3 "$(dirname "$0")/tm09_opmatch.py" "$W/entries.json" "$W/operator-sudo.json" "$W/canaries.json"
"$OSUDO" install -o root -g root -m 0600 "$W/operator-sudo.json" "$CONTROL/$SESSION-$NONCE-operator-sudo.json"
ops review "$MODE" "$SESSION" "$PORT" "$NONCE" "$DESK" "$CONTROL/$SESSION-$NONCE-operator-sudo.json"
"$OSUDO" -u "$SERVICE" "$ENGINE" review $ROLE_FLAGS $EXPORT_FLAGS --boundary "$OPS/$SESSION-$NONCE-review.json" \
  --probe-proof "$OPS/$SESSION-$NONCE-stopped-probe.json" "${ENGINE_FLAGS[@]}"
