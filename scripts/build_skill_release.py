"""Build a reproducible Skill-only ZIP from the checked-in allowlist."""
from __future__ import annotations
import argparse, hashlib, subprocess, zipfile
from pathlib import Path
FIXED_TIME=(1980,1,1,0,0,0); PREFIX="novel-distiller/"
def _tracked(root: Path) -> set[str]:
    data=subprocess.check_output(["git","ls-files","-z"],cwd=root)
    return {x.decode("utf-8") for x in data.split(b"\0") if x}
def resolve_allowlist(root: Path, allowlist: Path|None=None):
    tracked=_tracked(root); out=[]; allowlist=allowlist or root/"packaging/skill-release-files.txt"
    for raw in allowlist.read_text("utf-8").splitlines():
        item=raw.strip()
        if not item or item.startswith("#"): continue
        p=Path(item)
        if p.is_absolute() or ".." in p.parts or p.as_posix()!=item: raise ValueError("unsafe allowlist path")
        matches=[item] if not item.endswith("/**") else [x for x in tracked if x.startswith(item[:-3].rstrip("/")+"/")]
        if not matches: raise ValueError(f"allowlist path is missing: {item}")
        for name in matches:
            path=root/name
            if name not in tracked or not path.is_file() or path.is_symlink(): raise ValueError("untracked or unsafe release file")
            out.append(path)
    unique={p.relative_to(root).as_posix():p for p in out}
    return [unique[k] for k in sorted(unique)]
def build_release(root: Path, output: Path) -> str:
    files=resolve_allowlist(root); output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in files:
            info=zipfile.ZipInfo(PREFIX+path.relative_to(root).as_posix(),FIXED_TIME); info.create_system=3; info.external_attr=0o100644<<16; info.compress_type=zipfile.ZIP_DEFLATED; z.writestr(info,path.read_bytes())
    return hashlib.sha256(output.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output",required=True,type=Path); args=parser.parse_args(); print(build_release(Path.cwd(),args.output))
if __name__=="__main__": main()
