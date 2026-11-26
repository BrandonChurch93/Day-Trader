#!/bin/bash
# TM09 host wiring around tm09_operator and tm09_ops. Every root step goes through the timed operator sudo
# wrapper ($OSUDO), whose records ($OPLOG) the sudo review matches. Prints names and hashes only.
#
#   tm09_ops_host.sh launch      ROLE_ARGS SID PORT SIBLING BEARER_FILE
#       unique canary and signed launch boundary, listener in the background, ready line, live worker probe
#   tm09_ops_host.sh stop-review ROLE_ARGS SID PORT NONCE SIBLING BEARER_FILE
#       SIGTERM, stopped worker probe, sudo review from the log, signed review boundary, engine review
#
# ROLE_ARGS is one quoted word list without --role: "price_scout", "news_scout" or "boss MODEL ARM".
# BEARER_FILE is the worker's own 0600 copy (tm09_ops.py bearer-copy); the probe reads it as the worker account.
# TM09_MODE must be "rehearsal" or "production"; there is no default. Production also needs TM09_APPROVAL and,
# for news, TM09_EXPORT_DIR. The launch seal decides when production may run.
set -euo pipefail
case "${TM09_MODE:-}" in
  rehearsal|production) MODE=$TM09_MODE ;;
  *) echo "TM09_MODE must be rehearsal or production" >&2; exit 2 ;;
esac
OSUDO=${OSUDO:-/opt/tm07-ops-pub/osudo}
OPLOG=${OPLOG:-/tmp/tm07x/opsudo.jsonl}
PGREP=${PGREP:-pgrep}
REL=${TM09_RELEASE:-/opt/tm09-release-99c317e}
OPS_PY=${TM09_OPS_PY:-/opt/tm09-ops/tm09_ops.py}
LOGS=${TM09_LOGS:-/tmp/tm09x/logs}
WEEK=${TM09_WEEK:?TM09_WEEK required}
EXPORT_DIR=${TM09_EXPORT_DIR:-}
if [ "$MODE" = rehearsal ]; then
  APPROVAL=${TM09_APPROVAL:-/var/lib/tm09/ops/rehearsal-approval.json}; FLAG=(--rehearsal)
else
  APPROVAL=${TM09_APPROVAL:?production needs TM09_APPROVAL}; FLAG=()
fi
PY=(env -i PATH=/usr/bin:/bin PYTHONNOUSERSITE=1 "TM09_RELEASE=$REL" /usr/bin/python3.14 -B)

ops_root() { "$OSUDO" "${PY[@]}" "$OPS_PY" "$@"; }
role_flags() {  # ROLE_ARGS -> engine slot flags
  set -- $1
  case "$1" in
    price_scout|news_scout) [ $# = 1 ] || return 1; echo "--role $1" ;;
    boss) [ $# = 3 ] || return 1; echo "--role boss --boss $2 --arm $3" ;;
    *) return 1 ;;
  esac
}
export_flags() {  # production news scout reads the private headline export
  if [ "$MODE" = production ] && [ "${1%% *}" = news_scout ]; then
    [ -n "$EXPORT_DIR" ] || { echo "production news scout needs TM09_EXPORT_DIR" >&2; return 1; }
    echo "--export-dir $EXPORT_DIR"
  fi
}
engine() {
  "$OSUDO" -u tm09desk sh -c 'cd "$0" && exec env -i PATH=/usr/bin:/bin PYTHONNOUSERSITE=1 /usr/bin/python3.14 -B -m timemachine.tm09_operator "$@"' \
    "$REL" "$@" "${FLAG[@]}" --root /var/lib/tm09 --key-file /var/lib/tm09/operator.key --approval "$APPROVAL" --week "$WEEK"
}
probe_extra() { [ "$MODE" = production ] && [ -n "$EXPORT_DIR" ] && echo "$EXPORT_DIR" || true; }

cmd=${1:-}; shift || true
case $cmd in
launch)
  [ $# = 5 ] || { sed -n 2,13p "$0"; exit 2; }
  role=$1 sid=$2 port=$3 sib=$4 bearer=$5
  flags=$(role_flags "$role") || { echo "bad ROLE_ARGS" >&2; exit 2; }
  xflags=$(export_flags "$role")
  out=$(ops_root canary-launch "$sid" "$port")
  proof=$(echo "$out" | sed -n 1p); cap=$(echo "$out" | sed -n 2p | cut -d' ' -f1)
  nonce=$(basename "$proof" | sed -E "s/^$sid-([0-9a-f]{32})-proof.json$/\1/")
  [[ $nonce =~ ^[0-9a-f]{32}$ ]] || { echo "no canary proof" >&2; exit 1; }
  mkdir -p -m 700 "$LOGS"; log="$LOGS/$sid-$nonce.out"
  (set -m; nohup "$0" _serve "$flags $xflags" "$port" "/var/lib/tm09/ops/$cap" "$proof" >"$log" 2>&1 &)
  for _ in $(seq 30); do grep -q . "$log" 2>/dev/null && break; sleep 1; done
  echo "nonce $nonce"
  grep -qx "Registered desk ready; brief only this session's roles." "$log" || { cat "$log"; echo "listener not ready" >&2; exit 1; }
  ops_root probe "$MODE" live "$sid" "$port" "$nonce" "$sib" "$bearer" $(probe_extra) \
    || { echo "live probe failed; stopping the listener" >&2; "$0" _term "$role" "$port"; exit 1; }
  echo "ready, live probe passed" ;;
_serve)
  flags=$1 port=$2 cap=$3 proof=$4
  engine launch $flags --port "$port" --boundary "$cap" --canary-proof "$proof" ;;
_term)
  role=$1 port=$2
  pat="tm09_operator launch --role ${role%% *} .*--port $port( |$)"
  pid=$($PGREP -f "$pat") || { echo "no listener" >&2; exit 1; }
  [ "$(echo "$pid" | wc -w)" = 1 ] || { echo "more than one listener matched" >&2; exit 1; }
  "$OSUDO" kill -TERM "$pid"
  for _ in $(seq 20); do $PGREP -f "$pat" >/dev/null || exit 0; sleep 0.5; done
  echo "listener did not stop" >&2; exit 1 ;;
stop-review)
  [ $# = 6 ] || { sed -n 2,13p "$0"; exit 2; }
  role=$1 sid=$2 port=$3 nonce=$4 sib=$5 bearer=$6
  flags=$(role_flags "$role") || { echo "bad ROLE_ARGS" >&2; exit 2; }
  xflags=$(export_flags "$role")
  "$0" _term "$role" "$port"
  ops_root probe "$MODE" stopped "$sid" "$port" "$nonce" "$sib" "$bearer" $(probe_extra)
  desk=$("${PY[@]}" "$OPS_PY" slot-dir "$MODE" "$WEEK" "$role")
  ops_root review-boundary "$MODE" "$sid" "$port" "$nonce" "$desk" "$OPLOG" $(probe_extra)
  engine review $flags $xflags --boundary "/var/lib/tm09/ops/$sid-$nonce-review.json" \
    --probe-proof "/var/lib/tm09/ops/$sid-$nonce-stopped-probe.json" ;;
*) sed -n 2,13p "$0"; exit 2 ;;
esac
