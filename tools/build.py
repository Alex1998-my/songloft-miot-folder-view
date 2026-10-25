#!/usr/bin/env python3
"""Rebuild the folder-view distribution from a pinned upstream archive."""
import base64, hashlib, json, pathlib, zipfile, ast

ROOT = pathlib.Path(__file__).resolve().parents[1]
upstream = ROOT / 'vendor/miot-upstream-2026.10.25.1.jsplugin.zip'
provenance = json.loads((ROOT/'UPSTREAM.json').read_text())
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(upstream.read_bytes()) == provenance['archive_sha256'], 'Upstream archive differs from pinned input'
with zipfile.ZipFile(upstream) as z:
    files = {n:z.read(n) for n in z.namelist() if not n.endswith('/')}
jsname = next(n for n in files if n.endswith('.js'))
script = files.pop(jsname).decode()
assert script.count('fv=Ue({__name:"MainPage"') == 1
script = script.replace('fv=Ue({__name:"MainPage"', 'OriginalMain=Ue({__name:"MainPage"', 1)
assert script.count('hv="modulepreload"') == 1
script = script.replace('hv="modulepreload"', 'fv='+(ROOT/'src/folder-view.js').read_text().strip()+',hv="modulepreload"', 1)
customjs = 'static/js/folder-custom.'+sha(script.encode())[:12]+'.js'
files[customjs] = script.encode()
html = files['static/index.html'].decode().replace(jsname,customjs)
customcss = (ROOT/'src/folder-view.css').read_bytes()
cssname = 'static/css/folder-style.'+sha(customcss)[:12]+'.css'
files[cssname] = customcss
html = html.replace('</head>', '<link rel="stylesheet" href="'+cssname+'">\n</head>')
files['static/index.html'] = html.encode()
manifest = json.loads(files['plugin.json'])
manifest['version'] = '2026.10.26.2'
manifest['description'] = '社区定制：文件夹展开列表、直接点歌，保留原版视图。基于官方 2026.10.25.1。'
for key in ['updateUrl','download_url','zipHash']:
    manifest.pop(key,None)
manifest['entryHash'] = sha(files[manifest['main']])
manifest['zipHash'] = sha(''.join(n+'\n'+sha(files[n])+'\n' for n in sorted(files) if n!='plugin.json').encode())
files['plugin.json'] = (json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
dist=ROOT/'dist';dist.mkdir(exist_ok=True)
out=dist/'miot-folder-view.jsplugin.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for n,data in sorted(files.items()):
        info=zipfile.ZipInfo(n,(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,data)
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    actual=sha(''.join(n+'\n'+sha(z.read(n))+'\n' for n in sorted(z.namelist()) if n!='plugin.json').encode())
    assert actual==manifest['zipHash']
source='PLUGIN_DATA='+repr(base64.b64encode(out.read_bytes()).decode())+'\n'+(ROOT/'tools/install.py').read_text()
ast.parse(source)
installer=dist/'install-folder-view.command'
installer.write_text("#!/bin/bash\n/usr/bin/python3 -u <<'SONGLOFT_PYTHON_END'\n"+source+'\nSONGLOFT_PYTHON_END\n')
installer.chmod(0o755)
(dist/'SHA256SUMS').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in [out,installer]))
print('Built and validated:',out)
