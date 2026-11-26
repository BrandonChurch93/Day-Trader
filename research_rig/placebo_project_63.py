"""Exact-field projector, never a broad native-document JSON decoder."""
from gzip import GzipFile
from io import BytesIO
import os
from pathlib import PurePosixPath
import re
import stat

from count_63 import candidates, intersects_target, target_intervals
from placebo_63 import touches_deny
from placebo_native_63 import scan_page
from placebo_run_63 import PACKET, approved_scope, exact, file_in, hashed, money, need, read_projection, stamp, valid_pin


ARCHIVE_LIMIT = 12_000_000
MAX_UNCOMPRESSED_TOTAL = 96_000_000


def custodian_archive(relative):
    """Production loader; recursively no-follow, exclusively in the two partitions."""
    path = PurePosixPath(relative)
    need(not path.is_absolute() and len(path.parts) == 4 and
         path.parts[0] in ("placebo", "benchmark") and path.parts[1:3] == ("native", "bars_raw") and
         re.fullmatch(r"[\w.-]+\.json\.gz", path.name), "NATIVE_PATH")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(PACKET.parent, flags)
    try:
        for piece in path.parts[:-1]:
            meta = os.fstat(fd)
            need(stat.S_IMODE(meta.st_mode) == 0o700 and meta.st_uid == os.geteuid(), "FILE_POLICY")
            child = os.open(piece, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        meta = os.fstat(fd)
        need(stat.S_IMODE(meta.st_mode) == 0o700 and meta.st_uid == os.geteuid(), "FILE_POLICY")
        return file_in(fd, path.name)
    finally:
        os.close(fd)


def read_captured(page, partition, load_archive):
    exact(page, "file file_sha256 body_sha256 page_token next_page_token")
    path = PurePosixPath(page["file"])
    need(not path.is_absolute() and len(path.parts) == 4 and
         tuple(path.parts[:3]) == (partition, "native", "bars_raw") and
         re.fullmatch(r"[\w.-]+\.json\.gz", path.name), "NATIVE_PATH")
    packed = load_archive(str(path))
    need(type(packed) is bytes and 0 < len(packed) <= ARCHIVE_LIMIT, "NATIVE_BODY")
    with GzipFile(fileobj=BytesIO(hashed(packed, page["file_sha256"]))) as compressed:
        body = compressed.read(ARCHIVE_LIMIT + 1)
    need(0 < len(body) <= ARCHIVE_LIMIT, "NATIVE_BODY")
    return hashed(body, page["body_sha256"])


def chain_leaves(transport, manifest, approved, retained, sessions, successor_marks, deny, load_archive):
    """Generate all close locators from verified native page chain(s)."""
    exact(transport, "schema streams")
    need(transport["schema"] == "plan63-placebo-bar-transport-v1" and type(transport["streams"]) is list,
         "NATIVE_INDEX")
    wanted, stream_keys, paths, bodies, out, covered = {}, set(), set(), {}, {}, set()
    aliases = {x["subject_key"]: x for x in manifest["identity_map"]}
    source_rows, _, active_days, _ = candidates(retained, sessions)
    blocked = target_intervals(source_rows, active_days)
    for subject, d in successor_marks:
        blocked[subject].append((d, d))
    for (subject, start, end), m in approved.items():
        for side, d in (("entry", start), ("exit", end)):
            alias = m[f"{side}_alias"]
            if alias is not None:
                wanted.setdefault((subject, alias), set()).add((alias, d))

    sizes = 0
    for stream in transport["streams"]:
        exact(stream, "partition subject_key stable_security_id alias first last feed view pages")
        key = stream["subject_key"]
        partition = "benchmark" if key == "PCEF" else "placebo"
        a, b = stamp(stream["first"]), stamp(stream["last"])
        symbol = stream["alias"]
        bound = (key, a, b, symbol)
        ident = aliases.get(key)
        need(ident is not None and key in {k[0] for k in wanted} and
             stream["stable_security_id"] == ident["stable_security_id"] and stream["partition"] == partition and
             stream["feed"] == "sip" and stream["view"] == "raw" and a <= b and bound not in stream_keys and
             type(stream["pages"]) is list and stream["pages"], "NATIVE_STREAM")
        need(any(x["alias"] == symbol and stamp(x["from_session"]) <= a <= b <= stamp(x["through_session"])
                 for x in ident["dated_aliases"]), "NATIVE_ALIAS")
        need(key == "PCEF" or (not intersects_target(blocked, key, (a, b)) and
                               not touches_deny(deny, key, a, b)), "NATIVE_EMBARGO")
        stream_keys.add(bound)
        needs = {(sym, d) for sym, d in wanted.get((key, symbol), ()) if a <= d <= b}
        need(needs, "NATIVE_STREAM_EXTRA")
        covered.update((key, sym, d) for sym, d in needs)
        cursor, seen = None, set()
        for i, page in enumerate(stream["pages"]):
            body = read_captured(page, partition, load_archive)
            digest = page["body_sha256"]
            need(page["file"] not in paths and page["page_token"] == cursor and
                 (i == 0 or cursor is not None) and cursor not in seen, "NATIVE_PAGE_CHAIN")
            picked, following = scan_page(body, needs, (symbol, a, b))
            need(following == page["next_page_token"] and (following is None or type(following) is str),
                 "NATIVE_PAGE_CHAIN")
            paths.add(page["file"])
            seen.add(cursor)
            cursor = following
            if digest in bodies:
                need(bodies[digest] == body, "NATIVE_BODY")
            else:
                bodies[digest] = body
                sizes += len(body)
                need(sizes <= MAX_UNCOMPRESSED_TOTAL, "NATIVE_BODY_BUDGET")
            for (sym, d), leaf in picked.items():
                scoped = key, sym, d
                need(scoped not in out, "NATIVE_DUPLICATE_BAR")
                out[scoped] = leaf
        need(cursor is None, "NATIVE_PAGE_CHAIN")
    need(covered == {(key, sym, d) for (key, _), xs in wanted.items() for sym, d in xs}, "NATIVE_COVERAGE")
    return out, bodies


def single_token(ref, bodies):
    source = bodies[ref["body_sha256"]]
    start, size = ref["offset"], ref["length"]
    need(0 <= start < len(source) and 0 < size <= 50 and start + size <= len(source), "LEAF")
    token = source[start:start + size]
    if token.startswith(b'"') and token.endswith(b'"'):
        token = token[1:-1]
    value = token.decode("ascii")
    money(value)
    return value


def project(manifest, census, sessions, proofs, field_index, transport, preflight, *, load_archive=custodian_archive):
    """Preflight, transport, field index and evidence require exact audited pins.

    Generate an independent index from verified native raw pages then compare
    every supplied reference and all metadata before interpreting any price.
    Action amounts come only from exact typed, reconciled proof bytes.
    """
    approved, successors, retained, deny = approved_scope(manifest, census, sessions, proofs, preflight)
    scan, bodies = chain_leaves(transport, manifest, approved, retained, sessions, successors, deny, load_archive)
    wanted = {s for s, meta in approved.items() if meta["status"] == "present"}
    exact(field_index, "schema legs")
    need(field_index["schema"] == "plan63-placebo-leaf-index-v1" and type(field_index["legs"]) is list,
         "LEAF_INDEX")
    for (key, start, end), m in approved.items():
        actual = [scan.get((key, m[f"{side}_alias"], d)) for side, d in (("entry", start), ("exit", end))]
        endpoints_exist = all(bar is not None and bar["volume"] > 0 for bar in actual)
        need(endpoints_exist == (m["status"] == "present"), "NATIVE_MISSING_STATUS")
    staged = {}
    for row in field_index["legs"]:
        exact(row, "subject_key start end stable_security_id entry exit actions")
        scope = row["subject_key"], stamp(row["start"]), stamp(row["end"])
        need(scope in wanted and scope not in staged, "LEAF_SCOPE")
        m = approved[scope]
        issue = m["stable_security_id"]
        need(row["stable_security_id"] == issue, "IDENTITY")
        for side, d in (("entry", scope[1]), ("exit", scope[2])):
            # Exact equality includes close_ref digest, offset, length and
            # all nonprice fields; a caller cannot redirect to another token.
            need(row[side] == scan[(scope[0], m[f"{side}_alias"], d)], "LEAF_SCANNER_MISMATCH")
        actions, seen = [], set()
        need(type(row["actions"]) is list, "ACTION")
        last = scope[1], 1
        for a in row["actions"]:
            exact(a, "economic_action_sha256 ex_date kind")
            d, kind, proof = stamp(a["ex_date"]), a["kind"], a["economic_action_sha256"]
            order = (d, 0 if kind == "split" else 1)
            need(last < order and scope[1] < d <= scope[2] and kind in ("cash_usd", "split") and
                 valid_pin(proof) and proof not in seen, "ACTION")
            last = order
            seen.add(proof)
            receipt = proofs.require(proof, "action", issue, d, kind)
            actions.append({**a, "amount": receipt["canonical_amount"]})
        coverage = proofs.require(m["action_coverage_sha256"], "action_coverage", issue, scope[1], scope[2])
        need(seen == set(coverage["action_sha256s"]), "ACTION_COMPLETENESS")
        staged[scope] = row, actions
    need(set(staged) == wanted, "LEAF_SCOPE")
    proofs.complete()

    # The first numeric close interpretation is after complete validation.
    legs = []
    for _, (row, actions) in sorted(staged.items()):
        out = {k: row[k] for k in ("subject_key", "start", "end", "stable_security_id")}
        for side in ("entry", "exit"):
            b = row[side]
            out[side] = {**{k: b[k] for k in b if k != "close_ref"},
                         "raw_close": single_token(b["close_ref"], bodies)}
        out["actions"] = actions
        legs.append(out)
    payload = {"schema": "plan63-placebo-prices-v1", "legs": legs}
    read_projection(payload, approved, proofs)
    return payload
