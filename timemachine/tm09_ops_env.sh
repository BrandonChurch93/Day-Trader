# Shared setup for tm09_launch.sh and tm09_review.sh (sourced). Parameters the TM07 scripts hard-code.
OSUDO=${OSUDO:-/opt/tm07-ops-pub/osudo}
OPLOG=${OPLOG:-/tmp/tm07x/opsudo.jsonl}
PGREP=${PGREP:-pgrep}
need() { [ -n "${!1:-}" ] || { echo "$1 required${2:+ ($2)}" >&2; exit 2; }; }
need TM09_RELEASE "pinned release directory"; REL=$TM09_RELEASE
OPS_PY=${TM09_OPS_PY:-$REL/timemachine/tm09_ops_sudo.py}
LOGS=${TM09_LOGS:-/tmp/tm09x/logs}
BASE=/var/lib/tm09; SERVICE=tm09desk; OPS=$BASE/ops-v2; CONTROL=$BASE/control
usage() { sed -n 2,7p "$0" >&2; exit 2; }
ops() { "$OSUDO" env -i PATH=/usr/bin:/bin PYTHONNOUSERSITE=1 "TM09_RELEASE=$REL" /usr/bin/python3.14 -B "$OPS_PY" "$@"; }
setup() {
  [ $# -ge 4 ] || usage
  MODE=$1; ROLE=$2; SESSION=$3; PORT=$4
  need TM09_WEEK; WEEK=$TM09_WEEK
  [[ $SESSION =~ ^TM09-[0-9a-f]{32}$ ]] && [[ $PORT =~ ^880[1-6]$ ]] && [[ $WEEK =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || usage
  set -- $ROLE
  case "$1 $#" in
    "price_scout 1"|"news_scout 1") ROLE_FLAGS="--role $1"; SLOT=TM09-$WEEK-$1 ;;
    "boss 3") [[ $2 =~ ^[a-z0-9_]+$ && $3 =~ ^(P1|P2|N)$ ]] || usage; ROLE_FLAGS="--role boss --boss $2 --arm $3"; SLOT=TM09-$WEEK-$2-$3 ;;
    *) usage ;;
  esac
  case "$MODE" in
    rehearsal) RUN_CAPSULE=; APPROVAL=${TM09_APPROVAL:-$OPS/rehearsal-approval.json}; EXPORT_FLAGS=
               DESK=$BASE/invented-rehearsal/$SLOT; ENGINE_FLAGS=(--rehearsal) ;;
    production) need TM09_APPROVAL production; need TM09_EXPORT_DIR "production, every role"
               APPROVAL=$TM09_APPROVAL; RUN_CAPSULE=$APPROVAL
               EXPORT_FLAGS=; [ "${ROLE%% *}" = news_scout ] && EXPORT_FLAGS="--export-dir $TM09_EXPORT_DIR"
               DESK=$BASE/$SLOT; ENGINE_FLAGS=() ;;
    *) echo "MODE must be rehearsal or production" >&2; exit 2 ;;
  esac
  ENGINE_FLAGS+=(--root "$BASE" --key-file "$BASE/operator.key" --approval "$APPROVAL" --week "$WEEK")
}
stop_listener() {
  local pat="tm09_operator launch $ROLE_FLAGS .*--port $PORT( |$)" pid
  pid=$($PGREP -f "$pat") || { echo "no listener" >&2; return 1; }
  [ "$(echo "$pid" | wc -w)" = 1 ] || { echo "more than one listener matched" >&2; return 1; }
  "$OSUDO" kill -TERM "$pid"
  for _ in $(seq 20); do $PGREP -f "$pat" >/dev/null || return 0; sleep 0.5; done
  echo "listener did not stop" >&2; return 1
}
