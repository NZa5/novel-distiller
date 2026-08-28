from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import posixpath, stat, zipfile
@dataclass(frozen=True)
class EpubSecurityLimits:
 max_input_bytes:int=50*1024*1024; max_entries:int=5000; max_expanded_bytes:int=200*1024*1024; max_document_bytes:int=10*1024*1024; max_compression_ratio:float=100.0; max_nesting_depth:int=32
@dataclass(frozen=True)
class EpubManifest: entries:tuple[str,...]; total_bytes:int
def preflight_epub(path, limits=EpubSecurityLimits()):
 p=Path(path)
 if p.stat().st_size>limits.max_input_bytes: raise ValueError('ND-EPUB-LIMIT')
 try:
  with zipfile.ZipFile(p) as z:
   infos=z.infolist()
   if len(infos)>limits.max_entries: raise ValueError('ND-EPUB-LIMIT')
   total=0
   for i in infos:
    n=i.filename
    if '\x00' in n or n.startswith(('/', '\\')) or (len(n)>1 and n[1]==':') or '..' in posixpath.normpath(n).split('/') or stat.S_ISLNK(i.external_attr>>16): raise ValueError('ND-EPUB-UNSAFE-PATH')
    if i.flag_bits & 1: raise ValueError('ND-EPUB-ENCRYPTED')
    if i.compress_size and i.file_size/i.compress_size>limits.max_compression_ratio: raise ValueError('ND-EPUB-LIMIT')
    total+=i.file_size
    if total>limits.max_expanded_bytes or (n.lower().endswith(('.xhtml','.html','.xml')) and i.file_size>limits.max_document_bytes): raise ValueError('ND-EPUB-LIMIT')
    if n.lower().endswith(('.xhtml','.html','.xml')):
     data=z.read(i)
     if b'<!doctype' in data.lower() or b'<!entity' in data.lower(): raise ValueError('ND-EPUB-ACTIVE-CONTENT')
   if 'mimetype' not in z.namelist() or z.read('mimetype').strip()!=b'application/epub+zip': raise ValueError('ND-EPUB-MIMETYPE')
   return EpubManifest(tuple(i.filename for i in infos),total)
 except ValueError: raise
 except (zipfile.BadZipFile, OSError): raise ValueError('ND-EPUB-INVALID')
