"""Build original Coop Expanded assets from the manifest."""
import argparse
import contextlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from catalog import ROOT, WORK, checksum, entries, fingerprint, outputs, read, references, write
from contact_sheet import sheet
from validate import inspect

sys.path.insert(0,str(ROOT/"src"))


def blender():
    value=os.environ.get("BLENDER") or shutil.which("blender")
    if not value:
        base=Path(os.environ.get("ProgramFiles","C:/Program Files"))/"Blender Foundation"
        value=next(iter(sorted(base.glob("Blender */blender.exe"),reverse=True)),None)
    if not value: raise RuntimeError("Set BLENDER to Blender 4.2 or newer")
    return str(value)


@contextlib.contextmanager
def lock():
    WORK.mkdir(parents=True,exist_ok=True)
    with (WORK/"build.lock").open("a+b") as f:
        f.seek(0)
        if os.name=="nt":
            import msvcrt
            msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def build(e,cfg):
    i=e["id"]
    sig=fingerprint(e)
    base=dict(fingerprint=sig,category=e["category"],files=[],warnings=[])
    if e["group"]=="B":
        missing=references(e,cfg)
        if missing:
            return dict(base,status="skipped_no_reference",reason="Missing "+", ".join(missing))
        return dict(base,status="needs_fitting",reason="References present. Original fitted geometry, weighting and pose inspection required.")
    paths=outputs(e)
    work=WORK/i
    work.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work) as temp:
        stage=Path(temp)
        if e["group"]=="UI":
            from ui_art import generate
            sources=generate(e,stage)
            for src,path in zip(sources,paths,strict=True):
                path.parent.mkdir(parents=True,exist_ok=True)
                src.replace(path)
            measures={}
        else:
            directory=paths[0].parent
            directory.parent.mkdir(parents=True,exist_ok=True)
            dest=stage/i; dest.mkdir()
            with (work/"build.log").open("w",encoding="utf8") as log:
                run=subprocess.run([blender(),"-b","-t","3","--python-exit-code","1","--python",
                                    str(ROOT/"src"/"build_scene.py"),"--",i,sys.executable,str(dest),str(stage)],
                                   stdout=log,stderr=subprocess.STDOUT)
            if run.returncode:
                detail=(work/"build.log").read_text(encoding="utf8",errors="replace").splitlines()
                raise RuntimeError(next((s for s in reversed(detail) if "Error:" in s and "script failed" not in s),"Blender failed")+f" (assets/.work/{i}/build.log)")
            measures=read(stage/"metrics.json")
            backup=stage/"previous"
            if directory.exists(): directory.rename(backup)
            try: dest.rename(directory)
            except BaseException:
                if backup.exists(): backup.rename(directory)
                raise
        files=[p.relative_to(ROOT).as_posix() for p in paths]
        rec=dict(base,status="ok",**measures)
        rec.update(files=files,sha256={k:checksum(p) for k,p in zip(files,paths)})
        errors=inspect(e,rec,cfg,hashes=False)
        if errors: rec.update(status="validation_failed",reason=" | ".join(errors))
        return rec


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    selector=ap.add_mutually_exclusive_group(required=True)
    selector.add_argument("--all",action="store_true")
    selector.add_argument("--only",nargs="+",metavar="ID")
    selector.add_argument("--category",nargs="+",metavar="NAME")
    ap.add_argument("--force",action="store_true",help="Rebuild even when the source fingerprint matches")
    ap.add_argument("--jobs",type=int,default=2)
    args=ap.parse_args()
    items=entries()
    unknown=(set(args.only or [])-{e["id"] for e in items}) | (set(args.category or [])-{e["category"] for e in items})
    if unknown: ap.error("Unknown selection "+", ".join(sorted(unknown)))
    chosen=[e for e in items if args.all or e["id"] in (args.only or []) or e["category"] in (args.category or [])]
    with lock():
        cfg=read(ROOT/"conventions.json"); reportfile=ROOT/"asset_report.json"; report=read(reportfile,{})
        tasks=[]
        for e in chosen:
            prev=report.get(e["id"],{})
            if not args.force and prev.get("status")=="ok" and not inspect(e,prev,cfg):
                print("cached",e["id"],flush=True)
            else: tasks.append(e)
        with ThreadPoolExecutor(max_workers=max(1,args.jobs)) as pool:
            pending={pool.submit(build,e,cfg):e for e in tasks}
            for future in as_completed(pending):
                e=pending[future]
                try: rec=future.result()
                except Exception as err: rec=dict(status="failed",category=e["category"],files=[],warnings=[],reason=str(err))
                report[e["id"]]=rec
                write(reportfile,dict(sorted(report.items())))
                print(rec["status"],e["id"],rec.get("reason",""),flush=True)
        for cat in sorted({e["category"] for e in chosen}): sheet(cat)
        return int(any(report[e["id"]]["status"] not in ("ok","skipped_no_reference") for e in chosen))


if __name__=="__main__":
    sys.exit(main())
