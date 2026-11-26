# TM07 worker isolation probe

The operator runs this after preparing the actual deployment release and before starting any registered worker. This is a bounded sample using a disposable rehearsal with invented bars and tokens, and the provider wrapper in request-assembly mode without a model call. The sample tests nominated paths and one outbound destination, not all shared state or egress. Distinct OS identity tuples are not proof of disjoint access, and the launcher shim reports rather than independently proves request context. Deployed isolation, provider-internal memory and real tape coverage remain UNKNOWN until separately verified.

## Rehearsal inputs

- **Registered root:** An existing, empty, private off-repo root for the approved registration. Seal its absolute resolved path as `study_root`. It must not be inside the rehearsal root or vice versa.
- **Release:** Use the deployed launcher, executor policy, sandbox image or image manifest, and provider wrapper. List their absolute files as `release_files`, including the launcher command. Put the rehearsal endpoint in exactly the network lane the live desk will use. Worker mounts and permissions must match the proposed real deployment, with fixture/journal/scorer paths replaced by rehearsal canaries. Review those mounts and outbound policy independently; one TCP canary cannot prove a universal network ban.
- **Outbound canary:** Choose a private listener you control that accepts TCP from the operator and is not in the allowed desk lane. This records a denied connection, not a test against a public endpoint.

From the `dt-tm07` worktree, start the rehearsal service in the service namespace. The rehearsal root and ready file must not exist:

```sh
nice -n 10 python3 -B -m timemachine.tm07_isolation_probe rehearse \
  --rehearsal-root "$REHEARSAL_ROOT" --ready "$READY_FILE" --port "$DESK_PORT"
```

In a second terminal, make the private profile by copying the ready JSON and adding these fields. Change `desk_url` only if necessary to name the same rehearsal listener as seen from the real worker namespace.

```json
{
  "root": "/absolute/private/registered-root",
  "registration": "<sha256 digest of the approved registration body>",
  "launcher": ["/absolute/path/to/deployed-probe-shim"],
  "release_files": ["/absolute/path/to/deployed-probe-shim", "/absolute/path/to/launcher-policy-and-wrapper-manifest"],
  "egress_canary": {"host": "<operator-controlled internal address>", "port": 9001}
}
```

The existing ready file supplies `workers`, `scorer_only`, `rehearsal_root` and `desk_url`. Keep the profile, ready file, operator token directory and transcript out of Git. The shim must use the real launcher and never run the probe worker in its own operator context. Include the shim and all release inputs in the fingerprint; a change requires re-running the probe.

## Launcher contract

The collector invokes `<launcher ...> <identity> <fresh|handoff|reset>` with one JSON challenge on stdin. The eight identities are the two named scout roles and each of the two registered bosses in each of A/B/C. Only the role's rehearsal bearer is provided. The shim invokes `python3 -B -m timemachine.tm07_isolation_probe worker` inside that role's actual sandbox, with the original challenge plus `context` described below, and relays its one JSON result. Keep the role environments alive and distinct across the rehearsal so that changing only a label does not pass as isolation.

- **Fresh:** Assemble the first provider request without sending it. Derive the fields from the actual assembled input and enabled tools. Then load the supplied `marker` as invented same-role history through the normal handoff path, not through a separate probe-only input.
- **Handoff:** Assemble the next request with the normal same-role handoff. Return only the marker occurrences found in the actual request body. Fail if another role's marker is visible.
- **Reset:** Start a fresh provider request through the normal clean launch path. Confirm it carries no marker or provider conversation continuation identifier. Do not send it to a model.

Use `context = {"conversation_id": null, "memory_enabled": false, "tools": [...], "markers": [...]}`. Return only the allowed desk tool names from the real wrapper configuration, not a hardcoded pass assertion. Boss tools are `next`, `status`, `usage`, `look`, `pick`; scout tools are `next`, `status`, `usage`, `notes`. The expected marker list is empty on fresh/reset and the single role marker on handoff. Do not relay the whole request or credentials into the transcript.

## Collect, inspect and authorize

Run the collector with the production launcher policy, with the model send path off:

```sh
nice -n 10 python3 -B -m timemachine.tm07_isolation_probe collect \
  --profile "$PROFILE_FILE" --transcript "$TRANSCRIPT_FILE"
```

Inspect all 24 rows for the three phases of all eight identities. Every role needs a successful own route and denial on the wrong role, sibling session, legacy routes, fixture files, journals, scorer/token files and the outbound canary. Separately from the sample, an independent operator must review the actual launcher policy, effective mounts and permissions, shared writable state across roles and lifecycle phases, outbound lanes and sidecars, and how the wrapper assembles requests and passes context. Confirm the rehearsal uses equivalent policy and the same release as deployment. Record that review separately; do not treat a signed sample as a substitute. Seal the sampled transcript with the private operator key after inspection:

```sh
nice -n 10 python3 -B -m timemachine.tm07_isolation_probe seal \
  --transcript "$TRANSCRIPT_FILE" --key-file "$OPERATOR_KEY_FILE" --receipt "$RECEIPT_FILE"
```

The receipt is JSON with a `body` and `seal`. The body names `version`, `scope: "sampled-rehearsal-only"`, `root`, `registration`, `launcher_digest`, `probe_transcript_digest`, the distinct OS identity tuples, and the required sampled checks. An older receipt without this scope is not accepted. Stop the rehearsal listener and discard the rehearsal credentials. Only after independent review, the real-launcher rehearsal and explicit launch approval may the operator set `TM07_RUNS_DIR` to the registered root and call `server.serve_desk(port, approval_key=key, proof=receipt["body"], signature=receipt["seal"], launcher_digest=actual_release_digest)`. Compute `actual_release_digest` from the release files running now with `launch_fingerprint`, not by copying the digest from the receipt.
