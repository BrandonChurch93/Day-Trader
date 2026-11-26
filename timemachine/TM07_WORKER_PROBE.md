# TM07 same-host launch gate

Sibling agents run as `user` (uid 2000) on the operator's machine. The desk runs under a different Unix account. The registered root is mode 0700 and holds the week's tape copy, journals, notes, bearer records and scores. The listener binds only to loopback, requires the right bearer for every desk route, and offers no legacy routes. The probe samples these controls with made-up sessions and checks that uid 2000, without sudo, cannot list or traverse either study or rehearsal roots.

There is no worker launcher shim or provider wrapper. Give each new sibling a written brief with only its own bearer and, on handoff, only its own server handoff text. Tell it not to use sudo, web, direct prices, other workers' outputs or disk outside its assigned task. These are instructions, not controls. Compliance, provider-side memory, and whether a worker used other readable copies or the web are UNKNOWN. Passwordless sudo defeats ordinary Unix isolation if used. Sudo command logging is a spot check, not proof: both the operator and agents use the same uid, and an elevated process can alter logs. Review the deployment and test it on the actual host before approving any session.

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
REHEARSAL=$BASE/service/rehearsal-screen
READY=$BASE/service/ready-screen.json
REG=$BASE/service/registration.json
KEY=$BASE/service/operator.key
TRANSCRIPT=$BASE/control/transcript-screen.json
RECEIPT=$BASE/service/receipt-screen.json
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

Put this line in the file and check it with `visudo -c`. From the operator's uid-2000 terminal, run `sudo -n /usr/bin/true` once and confirm the new command appears in the log. A root-owned file alone does not prove sudo is configured to use it.

```sudoers
Defaults:user logfile="/var/log/tm07-sudo.log"
```

## Probe and start the server

Run from the root-owned release so neither account imports Python from a writable workspace. The command below starts a disposable, made-up listener as the desk account. It creates the rehearsal directory and ready file; both paths must not exist. The rehearsal and registered roots must be separate. Use the same loopback port that will serve the registered desk.

```sh
cd "$RELEASE"
export PYTHONNOUSERSITE=1
nice -n 10 /usr/sbin/runuser -u tm07desk -- "$PY" -B -m timemachine.tm07_isolation_probe rehearse +  --rehearsal-root "$REHEARSAL" --ready "$READY" --port "$PORT" &
REHEARSAL_PID=$!
```

Once the ready file exists, run the collector in the root shell. It invokes the probe itself as uid 2000 through `runuser`; it does not run any sudo command from that uid. Each probe invocation gets only a toy bearer in stdin. The transcript records checks, not bearers. Own routes must work, missing bearers and wrong-role and sibling-session bearer use must fail, and legacy routes must return 404. The operator confirms the named rehearsal controls actually exist before accepting an access denial. A missing file is not a passing denial.

```sh
nice -n 10 "$PY" -B -m timemachine.tm07_isolation_probe collect +  --ready "$READY" --root "$STUDY" --registration "$REG" +  --stage screen --transcript "$TRANSCRIPT"
less "$TRANSCRIPT"
less "$LOG"                     # review against your command record before attesting
nice -n 10 "$PY" -B -m timemachine.tm07_isolation_probe seal +  --transcript "$TRANSCRIPT" --key-file "$KEY" --receipt "$BASE/control/receipt-screen.json" +  --sudo-log-reviewed
install -o tm07desk -g tm07desk -m 0400 "$BASE/control/receipt-screen.json" "$RECEIPT"
kill "$REHEARSAL_PID"
wait "$REHEARSAL_PID" || true
nice -n 10 /usr/sbin/runuser -u tm07desk -- env TM07_RUNS_DIR="$STUDY" +  "$PY" -B -m timemachine.tm07_isolation_probe serve +  --port "$PORT" --receipt "$RECEIPT" --key-file "$KEY"
```

Start registered workers only after explicit approval. `serve_desk` verifies the receipt seal, registration binding, service uid, mode-0700 root, release, sudo log identity and stage. Old receipts are not accepted. The screen receipt permits only the three screen weeks, not the diagnostic or any extension week. Rerun the probe after a release, account, study-root, or sudo-log change. Never share the rehearsal credentials; discard them after the rehearsal.

## Check every session and lock the extension

Immediately before briefing any worker, confirm sudo is still logging with a known operator marker, inspect the root-owned log, and record its inode, byte offset and prefix hash. Keep your own time and exact sudo command record. After the session, inspect the new records and verify the original prefix before the session can count. For example, from the root shell:

```sh
# Before the briefing, after the separately issued operator marker:
stat -c '%d:%i %s %U %a' "$LOG"
less "$LOG"
OFFSET=$(stat -c '%s' "$LOG")
PREFIX=$(head -c "$OFFSET" "$LOG" | sha256sum)
# After the worker finishes, before treating the session as valid:
stat -c '%d:%i %s %U %a' "$LOG"
test "$(head -c "$OFFSET" "$LOG" | sha256sum)" = "$PREFIX"
tail -c "+$((OFFSET+1))" "$LOG"
```

Retain the checks with the private session records. Any unrecognized command, missing marker, changed prefix or log identity, truncated log, or unexplained gap blocks or invalidates the session. Matching entries to the operator's record is a human check, not identity attribution. Do not authorize concurrent privileged work by other people or agents.

**Fixed extension gate:** In addition to the existing 3/3 screen gate, every raw bar source or copy for the 17 extension weeks must be unreadable by uid 2000 without sudo throughout extension sessions. The screen may leave raw bars under `/home/user/workspace/rig` readable, as in TM06. Before issuing an extension receipt, inventory all host copies and put them behind a non-traversable directory outside any uid-2000-writable parent, or otherwise deny that uid access. One way to protect an inventoried directory after arranging lawful relocation and any required backups is `chown root:root "$PRIVATE_RAW"; chmod 0700 "$PRIVATE_RAW"`. Do not leave readable originals, caches, alternate exports, or overlapping tables. If a file mixes screen and extension bars, protect the whole file. Keep the week's service copy under `$STUDY`. Directory and file paths must be real and present; review completeness independently.

Repeat the rehearsal with unused extension paths and a new receipt filename. Replace the collect command with the following, passing each independent restricted directory or file. Seal and serve as above, with the new transcript and receipt. An extension receipt permits only the 17 extension weeks.

```sh
nice -n 10 "$PY" -B -m timemachine.tm07_isolation_probe collect +  --ready "$READY" --root "$STUDY" --registration "$REG" +  --stage extension --raw-bar "$PRIVATE_RAW" --transcript "$TRANSCRIPT"
nice -n 10 "$PY" -B -m timemachine.tm07_isolation_probe check-raw --receipt "$RECEIPT" --key-file "$KEY"
```

Run `check-raw` immediately before and after every extension session from the root shell, in addition to reviewing sudo. These checks sample access at their times. The operator must keep access denied between checks; do not restore access until all extension workers have stopped. A missing copy from the inventory, failed check, or unreadability that cannot be maintained blocks or invalidates the extension. Do not substitute weeks or make a claim using an unverified extension.
