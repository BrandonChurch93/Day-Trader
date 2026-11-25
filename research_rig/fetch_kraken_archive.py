"""Reads chosen files out of Kraken's published OHLCVT zip archives with HTTP range requests, so the whole archive need not be downloaded.
Usage, from research_rig/:
  python3 fetch_kraken_archive.py full      bitcoin and ether, daily and hourly, full history   -> data/kraken/full_*.csv   (rerun, replay 03)
  python3 fetch_kraken_archive.py 2026Q3    the same four files from one quarterly archive        -> data/kraken/2026Q3_*.csv
  python3 fetch_kraken_archive.py daily     every US dollar pair, daily bars, full history        -> data/kraken/daily/*.csv  (replay 04)
The folder is data/kraken unless KRAKEN_DIR is set. git ignores data/. Raw price files are never committed."""
import urllib.request, io, zipfile, sys, time, os
class Remote(io.RawIOBase):
    def __init__(self, urls):
        self.urls=urls; self.sizes=[]
        for u in urls:
            r=urllib.request.urlopen(urllib.request.Request(u,method="HEAD",headers={"User-Agent":"Mozilla/5.0"}),timeout=60); self.sizes.append(int(r.headers["Content-Length"]))
        self.total=sum(self.sizes); self.pos=0; self.nreq=0; self.nbytes=0
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self,off,whence=0):
        self.pos={0:off,1:self.pos+off,2:self.total+off}[whence]; return self.pos
    def _get(self,u,a,b):
        for i in range(4):
            try:
                r=urllib.request.urlopen(urllib.request.Request(u,headers={"Range":f"bytes={a}-{b}","User-Agent":"Mozilla/5.0"}),timeout=120); d=r.read()
                assert len(d)==b-a+1,(len(d),a,b); self.nreq+=1; self.nbytes+=len(d); return d
            except Exception as e: err=e; time.sleep(2)
        raise err
    def read(self,n=-1):
        if n<0: n=self.total-self.pos
        n=min(n,self.total-self.pos)
        if n<=0: return b""
        out=[]; start=self.pos; end=self.pos+n; base=0
        for u,s in zip(self.urls,self.sizes):
            lo=max(start,base); hi=min(end,base+s)
            if lo<hi: out.append(self._get(u,lo-base,hi-base-1))
            base+=s
        self.pos=end; return b"".join(out)
    def readinto(self,b):
        d=self.read(len(b)); b[:len(d)]=d; return len(d)
def extract(urls, wanted, outdir, tag):
    r=Remote(urls); z=zipfile.ZipFile(io.BufferedReader(r,buffer_size=4*1024*1024))
    names=z.namelist(); print(tag,"archive bytes",r.total,"files",len(names),flush=True)
    for w in wanted:
        m=[n for n in names if n.split("/")[-1]==w]
        if not m: print("  missing",w); continue
        d=z.read(m[0]); open(f"{outdir}/{tag}_{w}","wb").write(d); print("  got",m[0],len(d),flush=True)
    print(tag,"requests",r.nreq,"bytes fetched",r.nbytes,flush=True)
    return names
if __name__=="__main__":
    B="https://assets.kraken.com/marketing/institutions/"
    W=["XBTUSD_60.csv","XBTUSD_1440.csv","ETHUSD_60.csv","ETHUSD_1440.csv","MANIFEST.json"]
    which=sys.argv[1]; FULL=[B+f"Kraken_OHLCVT_Full.zip.part0{i}" for i in range(5)]
    K=os.environ.get("KRAKEN_DIR",os.path.join(os.path.dirname(os.path.abspath(__file__)),"data","kraken")); os.makedirs(os.path.join(K,"daily"),exist_ok=True)
    if which=="full": extract(FULL,W,K,"full")
    elif which=="daily":
        r=Remote(FULL); z=zipfile.ZipFile(io.BufferedReader(r,buffer_size=256*1024)); n=0
        infos=sorted([i for i in z.infolist() if i.filename.endswith("USD_1440.csv")],key=lambda i:i.header_offset)
        for i in infos:
            out=os.path.join(K,"daily",i.filename.split("/")[-1]); n+=1
            if os.path.exists(out) and os.path.getsize(out)==i.file_size: continue
            open(out,"wb").write(z.read(i))
            if n%50==0: print(n,len(infos),r.nreq,r.nbytes,flush=True)
        print("done",n,"files, requests",r.nreq,"bytes fetched",r.nbytes,flush=True)
    else: extract([B+f"Kraken_OHLCVT_{which}.zip"],W,K,which)
