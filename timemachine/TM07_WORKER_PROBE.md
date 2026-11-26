# TM07 same-host launch gate

Sibling agents run as `user` (uid 2000) on the operator's machine. The desk runs under a different Unix account. The registered root is mode 0700 and holds the week's tape copy, journals, notes, bearer records and scores. The listener binds only to loopback, requires the right bearer for every desk route, and offers no legacy routes. The probe samples these controls with made-up sessions and checks that uid 2000, without sudo, cannot list or traverse either study or rehearsal roots.

There is no worker launcher shim or provider wrapper. Give each new sibling a written brief with only its own bearer and, on handoff, only its own server handoff text. Tell it not to use sudo, web, direct prices, other workers' outputs or disk outside its assigned task. These are instructions, not controls. Compliance, provider-side memory, and whether a worker used other readable copies or the web are UNKNOWN. Passwordless sudo defeats ordinary Unix isolation if used. Sudo command logging is a spot check, not proof: both the operator and agents use the same uid, and an elevated process can alter logs. Review the deployment and test it on the actual host before approving any session.

**Soft, audited boundary (lead ruling 2026-11-26).** Passwordless sudo for uid 2000 stays on this host, because removing it could leave the host without an admin route, and a worker with web access could look up past prices anyway. The boundary is therefore declared soft and audited, not enforced. The launcher records `worker_passwordless_sudo: true` in every receipt as a fact, not a refusal. It requires, for every one of the 20 scored weeks: every listed price copy unreadable by uid 2000 without sudo, before the listener starts and after it stops; the sudo log present, root-owned and mode 0600; and the session's sudo log lines captured in the after file. After each week the operator checks three things: the sudo log against the operator's own timed command list (`review`, below), the server log, and the worker's own list of commands and addresses. Any worker sudo entry, any direct read of a price copy, or any outside price lookup voids that week for that arm. Operator sudo commands are listed with their times so they can be told apart.

## Prepare the host

The operator runs these commands, not a worker. Replace the Python path with the host's trusted, root-managed absolute executable for 3.14.8; do not point to code or an interpreter a sibling can replace. From the approved `dt-tm07` checkout, stage a read-only-to-workers release at a **new** directory. The following commands assume the service account, release directory and sudo log do not yet exist. On a repeat run, use a new release directory and new artifact filenames; do not truncate the existing sudo log.

```sh
RELEASE=/opt/tm07-release
REV=$(git rev-parse HEAD)
sudo install -d -o root -g root -m 0755 "$RELEASE"
git archive "$REV" | sudo tar --no-same-owner --no-same-permissions -xf - -C "$RELEASE"
sudo chmod -R go-w "$RELEASE"
sudo -i
```

In that root shell, set the paths, then create the account and directories. Keep the shell private; do not share it with a worker. Run session preparation, token issuance, and scoring under `tm07desk` into the private root, never into uid 2000's workspace. Copy in only the approved week inputs and the operator-controlled key and registration. Never put bearers or the signing key in command arguments, shell history, or a world-readable file.

```sh
RELEASE=/opt/tm07-release
PY=/usr/bin/python3.14   # substitute the verified host path
BASE=/var/lib/tm07
STUDY=$BASE/study
REG=$BASE/service/registration.json
KEY=$BASE/service/operator.key
LOG=/var/log/tm07-sudo.log
PORT=8765
umask 077
id user                          # must report uid 2000
"$PY" --version                  # must report Python 3.14.8
useradd --system --user-group --no-create-home --shell /usr/sbin/nologin tm07desk
install -d -o root -g root -m 0755 "$BASE"
install -d -o root -g root -m 0700 "$BASE/control"
install -d -o tm07desk -g tm07desk -m 0700 "$STUDY" "$BASE/service"
install -o tm07desk -g tm07desk -m 0600 /path/to/approved-registration.json "$REG"
install -o tm07desk -g tm07desk -m 0600 /path/to/operator-signing-key "$KEY"
install -o root -g root -m 0600 /dev/null "$LOG"  # first setup only
visudo -f /etc/sudoers.d/tm07-log
```

Put this line in the file and check it with `visudo -c`. Disable log wrapping so the complete canary command appears on one line. From the operator's uid-2000 terminal, run `sudo -n /usr/bin/true` once and confirm the new command appears in the log. A root-owned file alone does not prove sudo is configured to use it.

```sudoers
Defaults:user logfile="/var/log/tm07-sudo.log", loglinelen=0
```

## Probe and start the server

Run from the root-owned release so neither account imports Python from a writable workspace. Set SESSION to the exact, already prepared registered attempt ID and AUDIT to a new file in the root-only control directory. Review the existing sudo log against your command record before launching. Run one foreground launch per registered session; handoffs within that session use the same listener.

```sh
cd "$RELEASE"
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
read -r -p 'Registered session ID: ' SESSION
AUDIT="$BASE/control/$SESSION-$(date -u +%Y%m%dT%H%M%S).json"
less "$LOG"
```

Every one of the 20 scored weeks uses the same launch. Set PRIVATE_RAW to the protected price-copy inventory first (see "Check every session and lock the raw copies") and repeat `--raw-bar` for each further protected file or directory:

```sh
nice -n 10 "$PY" -B -m timemachine.tm07_isolation_probe launch \
  --root "$STUDY" --registration "$REG" --key-file "$KEY" --port "$PORT" \
  --session "$SESSION" --stage scored --audit "$AUDIT" --raw-bar "$PRIVATE_RAW"
```

The launcher makes a random nonce, starts a fresh toy listener as the service user on the intended port, tests the toy routes and file permissions as uid 2000, then shuts it down. The transcript contains results, not toy bearers. Permission checks do not read file contents. Missing files and readable files both fail, for different reasons.

The launcher makes and seals a receipt in memory, then sends it over a private pipe to the service process. No reusable receipt is written. The receipt is tied to the nonce, registration and session, study-root device and inode, service uid, port, stage, release, and fresh sudo checkpoint. It expires 10 minutes after the launch begins. The server consumes it atomically before listening; a replay or failed bind requires a fresh launch. The listener refuses a session outside the 20 scored weeks (for example the May diagnostic) before looking at week files. The receipt expiry is a startup limit, not a session duration limit.

## Check every session and lock the raw copies

Immediately before starting the registered listener, the launcher runs a harmless sudo command as uid 2000 with the launch nonce. It checks that the root-owned mode-0600 log grew, retained its prefix, and contains the exact new command. An empty log after that command or a missing line stops the launch. The launcher writes the pre-session size and SHA-256 hash to AUDIT before starting the listener. Brief workers only after explicit approval and the "Registered desk ready" line. When the session is done, stop the foreground launcher with Ctrl-C. It stops the listener and writes the post-session size and hash to the matching after file, checking the earlier prefix, together with every sudo log line added during the session (`sudo_entries`).

```sh
less "$AUDIT"
less "$AUDIT.after.json"
less "$LOG"
```

Keep your own time and exact sudo command record as a JSON list of `{"time": "<log timestamp>", "command": "<exact command>"}` and run the review. It prints VOID if any session sudo line does not match a listed time and command (each listed entry matches once), and writes the result next to the audit:

```sh
nice -n 10 "$PY" -B -m timemachine.tm07_isolation_probe review \
  --after "$AUDIT.after.json" --operator-sudo "$BASE/control/$SESSION-operator-sudo.json" --out "$AUDIT.review.json"
```

The review covers sudo only. The server log and the worker's own command and address list are checked by hand. A VOID, a direct price-copy read or an outside price lookup voids the week for that arm. Review the log before and after every session; do not count or score the session until this review and both audit files are complete. Any unrecognized command, changed prefix or log identity, truncated log, or unexplained gap blocks or invalidates the session. Matching entries to your record is a human check, not identity attribution. Whether anyone deliberately used sudo and edited the log as root remains UNKNOWN. Do not authorize concurrent privileged work by other people or agents.

**Raw-copy gate for all 20 weeks (ruling 2026-11-26):** the screen gate and the screen-stage exemption are gone. Every raw bar source or copy for the 20 scored weeks must be unreadable by uid 2000 without sudo throughout every scored session. Before issuing any receipt, inventory all host copies and put them behind a non-traversable directory outside any uid-2000-writable parent, owned by `tm07desk`, mode 0700. Do not leave readable originals, caches, alternate exports or overlapping tables. If a file mixes scored and other bars, protect the whole file. Keep the week's service copy under `$STUDY`. Directory and file paths must be real and present; review completeness independently. The launch checks access as uid 2000 immediately before starting the registered listener and again after stopping it. It refuses a readable path by name, opening and closing without reading any bytes.

These checks sample access at their times. The operator must keep access denied between checks; do not restore access until all workers have stopped. A missing copy from the inventory, a failed check, or unreadability that cannot be maintained blocks or invalidates the session. Do not substitute weeks.
