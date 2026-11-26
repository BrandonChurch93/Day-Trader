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

For a screen session:

```sh
nice -n 10 "$PY" -B -m timemachine.tm07_isolation_probe launch \
  --root "$STUDY" --registration "$REG" --key-file "$KEY" --port "$PORT" \
  --session "$SESSION" --stage screen --audit "$AUDIT"
```

The launcher makes a random nonce, starts a fresh toy listener as the service user on the intended port, tests the toy routes and file permissions as uid 2000, then shuts it down. The transcript contains results, not toy bearers. Permission checks do not read file contents. Missing files and readable files both fail, for different reasons.

The launcher makes and seals a receipt in memory, then sends it over a private pipe to the service process. No reusable receipt is written. The receipt is tied to the nonce, registration and session, study-root device and inode, service uid, port, stage, release, and fresh sudo checkpoint. It expires 10 minutes after the launch begins. The server consumes it atomically before listening; a replay or failed bind requires a fresh launch. The screen listener refuses out-of-stage routes before looking at week files. The receipt expiry is a startup limit, not a session duration limit.

## Check every session and lock the extension

Immediately before starting the registered listener, the launcher runs a harmless sudo command as uid 2000 with the launch nonce. It checks that the root-owned mode-0600 log grew, retained its prefix, and contains the exact new command. An empty log after that command or a missing line stops the launch. The launcher writes the pre-session size and SHA-256 hash to AUDIT before starting the listener. Brief workers only after explicit approval and the "Registered desk ready" line. When the session is done, stop the foreground launcher with Ctrl-C. It stops the listener and writes the post-session size and hash to the matching after file, checking the earlier prefix.

```sh
less "$AUDIT"
less "$AUDIT.after.json"
less "$LOG"
```

Keep your own time and exact sudo command record. Review the log before and after every session; do not count or score the session until this review and both audit files are complete. Any unrecognized command, changed prefix or log identity, truncated log, or unexplained gap blocks or invalidates the session. Matching entries to your record is a human check, not identity attribution. Whether anyone deliberately used sudo and edited the log as root remains UNKNOWN. Do not authorize concurrent privileged work by other people or agents.

**Fixed extension gate:** In addition to the existing 3/3 screen gate, every raw bar source or copy for the 17 extension weeks must be unreadable by uid 2000 without sudo throughout extension sessions. The screen may leave raw bars under `/home/user/workspace/rig` readable, as in TM06. Before issuing an extension receipt, inventory all host copies and put them behind a non-traversable directory outside any uid-2000-writable parent, or otherwise deny that uid access. One way to protect an inventoried directory after arranging lawful relocation and any required backups is `chown root:root "$PRIVATE_RAW"; chmod 0700 "$PRIVATE_RAW"`. Do not leave readable originals, caches, alternate exports, or overlapping tables. If a file mixes screen and extension bars, protect the whole file. Keep the week's service copy under `$STUDY`. Directory and file paths must be real and present; review completeness independently.

For an extension session, set the protected inventory path PRIVATE_RAW and use the extension launch below. Repeat the raw-bar argument for each additional independent protected file or directory. The same launch checks access as uid 2000 immediately before starting the registered listener and again after stopping it. It refuses a readable path by name, opening and closing without reading any bytes. An extension launch permits only the 17 extension weeks.

```sh
nice -n 10 "$PY" -B -m timemachine.tm07_isolation_probe launch \
  --root "$STUDY" --registration "$REG" --key-file "$KEY" --port "$PORT" \
  --session "$SESSION" --stage extension --audit "$AUDIT" --raw-bar "$PRIVATE_RAW"
```

These checks sample access at their times. The operator must keep access denied between checks; do not restore access until all extension workers have stopped. A missing copy from the inventory, failed check, or unreadability that cannot be maintained blocks or invalidates the extension. Do not substitute weeks or make a claim using an unverified extension.
