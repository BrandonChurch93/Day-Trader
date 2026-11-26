#!/bin/bash
# TM09 copy of the TM07 launcher (/opt/tm07-ops/launch.sh). Parameters instead of TM07 constants: mode, study
# root, service user, port, release. Every root step goes through the timed operator sudo wrapper ($OSUDO).
# usage: tm09_launch.sh MODE "ROLE_ARGS" SESSION PORT SIBLING BEARER_FILE
#   MODE rehearsal|production (no default); ROLE_ARGS price_scout | news_scout | "boss MODEL ARM"
#   env: TM09_WEEK (required), TM09_APPROVAL (production), TM09_EXPORT_DIR (production, every role)
set -euo pipefail
. "$(dirname "$0")/tm09_ops_env.sh"
setup "$@"
[ $# = 6 ] || usage
SIB=$5; BEARER=$6
ops preflight "$MODE" ${RUN_CAPSULE:+"$RUN_CAPSULE"}
out=$(ops checkpoint "$SESSION" "$PORT")
PROOF=$(echo "$out" | sed -n 1p); CAP=$OPS/$(echo "$out" | sed -n 2p | cut -d' ' -f1)
NONCE=$(basename "$PROOF" | sed -E "s/^$SESSION-([0-9a-f]{32})-proof.json$/\1/")
[[ $NONCE =~ ^[0-9a-f]{32}$ ]] || { echo "no canary proof" >&2; exit 1; }
mkdir -p -m 700 "$LOGS"; LOG=$LOGS/$SESSION-$NONCE.out
(set -m; nohup "$OSUDO" -u "$SERVICE" sh -c 'cd "$0" && exec env -i PATH=/usr/bin:/bin PYTHONNOUSERSITE=1 nice -n 10 /usr/bin/python3.14 -B -m timemachine.tm09_operator "$@"' \
  "$REL" launch $ROLE_FLAGS $EXPORT_FLAGS --port "$PORT" --boundary "$CAP" --canary-proof "$PROOF" "${ENGINE_FLAGS[@]}" \
  >"$LOG" 2>&1 </dev/null &)
for _ in $(seq 30); do grep -q . "$LOG" 2>/dev/null && break; sleep 1; done
echo "nonce $NONCE"
grep -qx "Registered desk ready; brief only this session's roles." "$LOG" || { cat "$LOG" >&2; echo "listener not ready" >&2; exit 1; }
ops probe live "$SESSION" "$PORT" "$NONCE" "$SIB" "$BEARER" || { echo "live probe failed; stopping" >&2; stop_listener; exit 1; }
echo "ready, live probe passed"
