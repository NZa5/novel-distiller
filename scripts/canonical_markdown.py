import base64,html,json,re
BIDI=dict.fromkeys(map(ord,'\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069'),None)
HEADINGS={'en':['Scope & metadata','Executive summary','Characters','Plot','Relationships','Foreshadowing','Timeline','Style','Uncertainties & contradictions','Coverage & quality check'],'zh-CN':['范围与元数据','核心摘要','人物','情节','人物关系','伏笔','时间线','风格','不确定项与矛盾','覆盖范围与质量检查']}
def safe_scalar(v):
 t=str(v).translate(BIDI);t=''.join(c for c in t if c in '\n\t' or ord(c)>=32 and not 127<=ord(c)<=159);t=html.escape(t)
 for c in "\\`*_{}[]()#+-.!|":t=t.replace(c,"\\"+c)
 return re.sub(r'(?i)\b(?:https?|javascript|file):',lambda m:m.group(0).replace(':','&#58;'),t)
def _san(x):
 if isinstance(x,str):return safe_scalar(x)
 if isinstance(x,list):return [_san(v) for v in x]
 if isinstance(x,dict):return {k:_san(v) for k,v in x.items()}
 return x
def render_markdown(d):
 lang='zh-CN' if d['metadata']['output_language'].startswith('zh') else 'en'; h=HEADINGS[lang]; safe=_san(d)
 keys=['metadata','summary','characters','plots','relationships','foreshadowing','timeline','style','uncertainties','quality'];out=['# Novel Distiller 2.0','']
 for title,key in zip(h,keys):
  out += [f'## {title}','',f'<!-- canonical:{key} -->','```json',json.dumps(safe[key],ensure_ascii=False,sort_keys=True,indent=2),'```','']
 out += ['<!-- canonical-document-base64',base64.b64encode(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).decode(),'-->','']
 return '\n'.join(out)
def parse_markdown(t):
 m=re.search(r'<!-- canonical-document-base64\n(.*?)\n-->',t,re.S)
 if not m:raise ValueError('invalid canonical Markdown')
 return json.loads(base64.b64decode(m.group(1)).decode())
