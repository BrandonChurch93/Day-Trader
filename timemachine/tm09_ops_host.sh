#!/bin/bash
# TM09 host wiring around tm09_operator and tm09_ops. Every root step goes through the timed operator sudo
# wrapper ($OSUDO), whose records ($OPLOG) the sudo review matches. Prints names and hashes only.
#
#   tm09_ops_host.sh launch ROLE_ARGS SID PORT                   canary, signed launch boundary, background listener
#   tm09_ops_host.sh stop-review ROLE_ARGS SID PORT NONCE SIBLING BEARER_FILE
#                                                                SIGTERM, stopped probe, sudo review, review boundary, desk review
# ROLE_ARGS is one quoted word list: "price_scout", "news_scout" or "boss --boss MODEL --arm P1|P2|N".
# BEARER_FILE is the worker's own 0600 copy, read only by the isolation probe as the worker account.
# Add --rehearsal through TM09_MODE=--rehearsal; the launch seal decides the production flags.
set -euo pipefail
OSUDO=${OSUDO:-/opt/tm07-ops-pub/osudo}
OPLOG=${OPLOG:-/tmp/tm07x/opsudo.jsonl}
REL=${TM09_RELEASE:-/opt/tm09-release-99c317e}
OPS_PY=${TM09_OPS_PY:-/opt/tm09-ops/tm09_ops.py}
LOGS=${TM09_LOGS:-/tmp/tm09x/logs}
MODE=${TM09_MODE:---rehearsal}
WEEK=${TM09_WEEK:-2026-09-07}
APPROVAL=${TM09_APPROVAL:-/var/lib/tm09/ops/rehearsal-approval.json}
CANARIES=(--canary /var/lib/tm09/operator.key --canary "$APPROVAL")
PY="env -i PATH=/usr/bin:/bin PYTHONNOUSERSITE=1 TM09_RELEASE=$REL /usr/bin/python3.14 -B"

as_desk() { "$OSUDO" -u tm09desk $PY "$@"; }
as_root() { "$OSUDO" $PY "$@"; }
operator() {
  "$OSUDO" -u tm09desk sh -c 'cd "$0" && exec env -i PATH=/usr/bin:/bin PYTHONNOUSERSITE=1 /usr/bin/python3.14 -B -m timemachine.tm09_operator "$@"' \
    "$REL" "$@" $MODE --root /var/lib/tm09 --key-file /var/lib/tm09/operator.key --approval "$APPROVAL" --week "$WEEK"
}
desk_dir() {  # ROLE_ARGS -> slot directory name
  set -- $1
  local base=/var/lib/tm09/$([ "$MODE" = --rehearsal ] && echo invented-rehearsal || echo study)
  if [ "$1" = boss ]; then echo "$base/TM09-$WEEK-$3-$5"; else echo "$base/TM09-$WEEK-$1"; fi
}

cmd=$1; shift
case $cmd in
launch)
  role=$1 sid=$2 port=$3
  proof=$(as_root "$OPS_PY" canary "$sid" "$port" | cut -d' ' -f1)
  nonce=$(basename "$proof" | sed -E "s/^$sid-([0-9a-f]{32})-proof.json$/\1/")
  cap=$(as_desk "$OPS_PY" launch-boundary "$sid" "$port" "$proof" | cut -d' ' -f1)
  mkdir -p -m 700 "$LOGS"
  out="$LOGS/$sid-$nonce.out"
  (set -m; nohup "$0" _serve "$role" "$port" "/var/lib/tm09/ops/$cap" "$proof" >"$out" 2>&1 &)
  for _ in $(seq 30); do grep -q . "$out" 2>/dev/null && break; sleep 1; done
  echo "nonce $nonce"; cat "$out" ;;
_serve)
  role=$1 port=$2 cap=$3 proof=$4
  operator launch $role --port "$port" --boundary "$cap" --canary-proof "$proof" ;;
stop-review)
  role=$1 sid=$2 port=$3 nonce=$4 sib=$5 bearer=$6
  first=${role%% *}
  pat="tm09_operator launch --role $first( .*)? --port $port( |$)"
  pid=$(pgrep -f "$pat")
  "$OSUDO" kill -TERM $pid
  for _ in $(seq 20); do pgrep -f "$pat" >/dev/null || break; sleep 0.5; done
  mkdir -p -m 700 "$LOGS"; probe="$LOGS/$sid-$nonce-probe.json"
  (cd "$REL" && umask 077 && env -i PATH=/usr/bin:/bin /usr/bin/python3.14 -B -m timemachine.tm09_isolation_probe \
     --port "$port" --session "$sid" --sibling "$sib" --bearer-file "$bearer" --stopped "${CANARIES[@]}" >"$probe")
  cat "$probe"
  "$OSUDO" install -o tm09desk -g tm09desk -m 0600 "$probe" "/var/lib/tm09/ops/$sid-$nonce-probe.json"
  as_root "$OPS_PY" sudo-review "$sid" "$nonce" "$OPLOG"
  as_desk "$OPS_PY" review-boundary "$sid" "$port" "$nonce" "$(desk_dir "$role")" \
     "/var/lib/tm09/ops/$sid-$nonce-probe.json" "/var/lib/tm09/ops/$sid-$nonce-sudo.json"
  operator review $role --boundary "/var/lib/tm09/ops/$sid-$nonce-review.json" --probe-proof "/var/lib/tm09/ops/$sid-$nonce-probe.json" ;;
*) sed -n 2,12p "$0"; exit 2 ;;
esac
