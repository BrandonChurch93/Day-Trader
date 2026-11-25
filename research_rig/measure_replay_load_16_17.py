"""Load verified real archives for RSS only. No scoring, locks or return calculations."""
import argparse
from pathlib import Path
import resource

try:
    from . import score_16 as A, score_17 as B
except ImportError:
    import score_16 as A
    import score_17 as B


def measure(replay,data,identity_path):
    F = A.F
    F.DATA = data
    F.F.DATA = data.parent/"replay_13"
    p13,p = F.config()
    policy=F.json_read(identity_path)
    for name,sha in policy["archive_manifest_sha256"].items():
        if F.digest((data/name).read_bytes())!=sha:
            raise ValueError("identity manifest hash changed")
    viewed=F.json_read(data/"manifest_futures.json")
    spot=F.json_read(data/"manifest_spot.json")
    cut=A.funding_cutoff(p,p13,A.source_ranges(viewed))
    runtime=p|{"end":F.F.utc(cut).date().isoformat()}
    allowed=A.I.Timeline(policy,cut).admitted(runtime)
    futures=viewed if replay==16 else B.combine_futures(
        viewed,F.json_read(data/"manifest_futures_held.json"),policy["snapshots_sha256"])
    # Do not call either scorer's run() or either engine. Keep both loaded
    # markets allocated until after the high-water mark is read.
    spots=A.load_groups(A.admitted_archives(spot,allowed["spot"],True),True,cut)
    perps=A.load_groups(A.admitted_archives(futures,allowed["futures"],False),False,cut)
    print("replay",replay,"spot groups",len(spots),"perp groups",len(perps),
          "peak RSS KiB",resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("replay",type=int,choices=(16,17))
    p.add_argument("data",type=Path)
    p.add_argument("identity",type=Path)
    x=p.parse_args()
    measure(x.replay,x.data,x.identity)
