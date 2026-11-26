"""Plan 43 attempt 3: exact quantization intervals; no venue, I/O, or return logic."""
from collections import defaultdict
from fractions import Fraction


HALF_TICK = Fraction(1, 200)
SLACK = Fraction(1, 100_000_000)
ERROR = HALF_TICK + SLACK
FACTOR_EPS = Fraction(1, 10000)


def intersect(a,b):
    lo=max(a[0],b[0])
    hi=min(x for x in (a[1],b[1]) if x is not None) if a[1] is not None or b[1] is not None else None
    return (lo,hi) if hi is None or (hi>=lo and hi>0) else None


def interval(source,target,source_error=0):
    """Feasible positive target/source factors for all four latent prices."""
    result=(Fraction(0),None)
    for src,dst in zip(map(Fraction,source.flat_key),map(Fraction,target.flat_key)):
        bound=(max(Fraction(0),dst-ERROR)/(src+source_error),
               (dst+ERROR)/(src-source_error) if src>source_error else None)
        result=intersect(result,bound)
        if result is None:
            break
    return result


def constrain(anchor,observed,change=Fraction(1)):
    """Common initial factor allowing rounding uncertainty and the frozen 1 bp band."""
    normal=(observed[0]/change,observed[1]/change if observed[1] is not None else None)
    if anchor is None:
        return normal
    slack=(normal[0]/(1+FACTOR_EPS),normal[1]/(1-FACTOR_EPS) if normal[1] is not None else None)
    return intersect(anchor,slack)


def volume_agrees(a,b,dates):
    ratios=[Fraction(a[d].v)/Fraction(b[d].v) for d in dates]
    return len(ratios)>=3 and 100*sum(abs(y/x-1)<Fraction(1,100) for x,y in zip(ratios,ratios[1:]))>=98*(len(ratios)-1)


def diagnose(raw,entry,filing,scope,seq,positive,note,skip=lambda key:None):
    """Check independently available view pairs and retain all shape/factor evidence."""
    actions=defaultdict(list)
    for day,kind,amount,*_ in seq:
        actions[day].append((kind,Fraction(amount)))
    shaped=[]
    gaps=set()
    for name,source,dest,source_error,uses_actions in (
            ("raw_entry",raw,entry,0,True),("raw_filing",raw,filing,0,False),
            ("adjusted_pair",entry,filing,ERROR,False)):
        prior=None
        anchor=None
        change=Fraction(1)
        for i,day in enumerate(scope):
            if not (positive(source,day) and positive(dest,day)):
                skip("ohlc_shape")
                if name!="raw_filing":
                    skip("raw_factor" if uses_actions else "asof_factor")
                continue
            if uses_actions and prior is not None:
                unknown=False
                for j in range(prior+1,i+1):
                    step=actions[scope[j]]
                    split=next((value for kind,value in step if kind=="split"),None)
                    cash=sum(value for kind,value in step if kind!="split")
                    if split is not None:
                        change*=split
                    elif cash:
                        if not positive(raw,scope[j-1]):
                            skip("cash_factor")
                            unknown=True
                            gaps.add(scope[j])
                        else:
                            previous=Fraction(raw[scope[j-1]].c)
                            if note("cash_factor",previous>cash,"DIVIDEND_BASIS"):
                                change/=1-cash/previous
                            else:
                                unknown=True
                if unknown:
                    anchor,change=None,Fraction(1)
            prior=i
            feasible=interval(source[day],dest[day],source_error)
            if not note("ohlc_shape",feasible is not None,"OHLC_TICK"):
                shaped.append((name,day.isoformat()))
                if name!="raw_filing":
                    skip("raw_factor" if uses_actions else "asof_factor")
                continue
            if name=="raw_filing":
                continue  # The two frozen time-series anchors remain raw/entry and entry/filing.
            merged=constrain(anchor,feasible,change)
            factor="RAW_BASIS_CHANGE" if uses_actions else "ASOF_BASIS_CHANGE"
            if note("raw_factor" if uses_actions else "asof_factor",merged is not None,factor):
                anchor=merged
    return shaped,sorted(gaps)
