from pathlib import Path
import argparse,hashlib,zipfile
FIXED=(1980,1,1,0,0,0)
def resolve(root):
 out=[]
 for line in (root/'packaging/skill-release-files.txt').read_text('utf8').splitlines():
  line=line.strip()
  if not line:continue
  if '..' in line or Path(line).is_absolute():raise ValueError('unsafe allowlist')
  if line.endswith('/**'):out += [p for p in (root/line[:-3]).rglob('*') if p.is_file()]
  elif (root/line).is_file():out.append(root/line)
 return sorted(set(out),key=lambda p:p.relative_to(root).as_posix())
def build_release(root,output):
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in resolve(root):
   i=zipfile.ZipInfo('novel-distiller/'+p.relative_to(root).as_posix(),FIXED);i.create_system=3;i.external_attr=0o100644<<16;i.compress_type=zipfile.ZIP_DEFLATED;z.writestr(i,p.read_bytes())
 return hashlib.sha256(output.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(build_release(Path.cwd(),a.output))
if __name__=='__main__':main()
