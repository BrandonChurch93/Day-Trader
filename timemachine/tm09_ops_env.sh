# Shared setup for tm09_launch.sh and tm09_review.sh (sourced). Parameters the TM07 scripts hard-code.
OSUDO=/opt/tm07-ops-pub/osudo
PGREP=pgrep
TM07_PORTS="8781 8782 8783 8784 8785 8786 8787"
need() { [ -n "${!1:-}" ] || { echo "$1 required${2:+ ($2)}" >&2; exit 2; }; }
need TM09_RELEASE "pinned release directory"; REL=$TM09_RELEASE
OPS_PY=$REL/timemachine/tm09_ops_sudo.py; ENGINE=$REL/timemachine/tm09_engine.sh
LOGS=/tmp/tm09x/logs
BASE=/var/lib/tm09; SERVICE=tm09desk; OPS=$BASE/ops-v2; CONTROL=$BASE/control
usage() { sed -n 2,7p "$0" >&2; exit 2; }
ops() { "$OSUDO" env -i PATH=/usr/bin:/bin PYTHONNOUSERSITE=1 "TM09_RELEASE=$REL" /usr/bin/python3.14 -B "$OPS_PY" "$@"; }
no_tm07() {  # TM09 runs only when no TM07 session is open (lead ruling): refuse if any TM07 listener port answers
  local p
  for p in $TM07_PORTS; do
    if (exec 3<>"/dev/tcp/127.0.0.1/$p") 2>/dev/null; then echo "TM07 listener on $p answers; TM09 refuses" >&2; exit 3; fi
  done
}
setup() {
  [ $# -ge 4 ] || usage
  MODE=$1; ROLE=$2; SESSION=$3; PORT=$4
  need TM09_WEEK; WEEK=$TM09_WEEK
  [[ $SESSION =~ ^TM09-[0-9a-f]{32}$ ]] && [[ $PORT =~ ^880[1-6]$ ]] && [[ $WEEK =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || usage
  set -- $ROLE
  case "$1 $#" in
    "price_scout 1"|"news_scout 1") ROLE_FLAGS="--role $1"; SLOT=TM09-$WEEK-$1 ;;
    "boss 3") [[ $2 =~ ^[a-z0-9_]+$ && $3 =~ ^(P[123]|N[123]?)$ ]] || usage; ROLE_FLAGS="--role boss --boss $2 --arm $3"; SLOT=TM09-$WEEK-$2-$3 ;;
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
  no_tm07
}
stop_listener() {  # only this launch's generation: the pattern names its nonce-bound boundary file
  local pat="tm09_operator launch $ROLE_FLAGS .*--port $PORT --boundary $OPS/$SESSION-$NONCE-launch.json( |$)" pid
  pid=$($PGREP -f "$pat") || { echo "no listener" >&2; return 1; }
  [ "$(echo "$pid" | wc -w)" = 1 ] || { echo "more than one listener matched" >&2; return 1; }
  "$OSUDO" kill -TERM "$pid"
  for _ in $(seq 20); do $PGREP -f "$pat" >/dev/null || return 0; sleep 0.5; done
  echo "listener did not stop" >&2; return 1
}
