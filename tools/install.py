import sys
def tty_input(prompt):
    print(prompt, end='', flush=True)
    with open('/dev/tty', 'r') as tty:
        return tty.readline().rstrip('\n')
import base64, json, urllib.request, urllib.error, getpass, uuid
BASE = ''
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
def request(path, data, headers):
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method='POST')
    try:
        with OPENER.open(req,timeout=180 if path.endswith("/upload") else 20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError('HTTP %s: %s'%(e.code,e.read().decode('utf-8',errors='replace'))) from None
def main():
    global BASE
    from urllib.parse import urlparse
    BASE=tty_input('请输入 Songloft 地址（例如 http://nas.local:58091）：').strip().rstrip('/')
    parsed=urlparse(BASE)
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('请输入完整的 http:// 或 https:// 地址，地址中不要包含账号密码')
    if 'PLUGIN_DATA' not in globals():
        from pathlib import Path
        globals()['PLUGIN_DATA']=base64.b64encode((Path(__file__).resolve().parents[1]/'dist/miot-folder-view.jsplugin.zip').read_bytes()).decode()
    print('安装文件夹视图 v2026.10.26.2（已补齐校验值）到：'+BASE)
    print('正在检查 NAS 连接（直接连接，不使用系统代理）…', flush=True)
    with OPENER.open(BASE+'/api/v1/version',timeout=10) as r:
        version=json.loads(r.read())
    print('连接成功，Songloft 版本：'+str(version.get('version','未知')), flush=True)
    print('会更新现有智能音箱插件；沿用账号和设备配置。')
    print('请输入 Songloft 登录信息（不是小米账号）。密码不显示、不保存。')
    username=tty_input('Songloft 用户名 [admin]：').strip() or 'admin'
    password=getpass.getpass('Songloft 密码：')
    print('第 1 步：正在登录 Songloft（最多等待 20 秒）…', flush=True)
    auth=request('/api/v1/auth/login',json.dumps({'username':username,'password':password}).encode(),{'Content-Type':'application/json'})
    password=None
    print('登录成功。', flush=True)
    data=auth.get('data',auth)
    token=data.get('access_token') or data.get('token') or auth.get('access_token') or auth.get('token')
    if not token: raise RuntimeError('登录响应没有返回访问令牌，请检查登录是否成功。')
    boundary='----SongloftInstaller'+uuid.uuid4().hex
    payload=base64.b64decode(PLUGIN_DATA)
    body=('--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="miot.jsplugin.zip"\r\nContent-Type: application/zip\r\n\r\n').encode()+payload+('\r\n--'+boundary+'--\r\n').encode()
    print('第 2 步：正在上传并更新插件（最多等待 3 分钟）…', flush=True)
    try:
        result=request('/api/v1/jsplugins/upload',body,{'Authorization':'Bearer '+token,'Content-Type':'multipart/form-data; boundary='+boundary})
    except Exception as upload_error:
        print('上传等待失败，继续检查服务器是否已更新：'+str(upload_error), flush=True)
        result={'failed':1,'message':str(upload_error)}
    print('\n服务端返回：', flush=True)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('第 3 步：检查服务器插件版本…', flush=True)
    req=urllib.request.Request(BASE+'/api/v1/jsplugins',headers={'Authorization':'Bearer '+token})
    with OPENER.open(req,timeout=15) as response:
        plugins=json.loads(response.read())
    def find_miot(value):
        if isinstance(value,dict):
            if value.get('entryPath',value.get('entry_path'))=='miot':
                return value
            for child in value.values():
                found=find_miot(child)
                if found: return found
        elif isinstance(value,list):
            for child in value:
                found=find_miot(child)
                if found: return found
    installed=find_miot(plugins)
    if installed:
        print('服务器中智能音箱版本：'+str(installed.get('version','未知')), flush=True)
        if installed.get('version')=='2026.10.26.2':
            result={'success':1,'failed':0}
        else:
            result={'failed':1,'message':'服务器仍是旧版本，更新未完成'}
    if result.get('failed',0) or any(not x.get('success',False) for x in result.get('results',[])):
        print('\n插件安装未成功，请把上方错误内容发给我。')
    else:
        print('\n上传已完成。请刷新 Songloft → 设置 → 导航与插件，检查“智能音箱”是否已出现并启用。')
try:
    main()
except Exception as e:
    print('\n未完成：'+str(e))
    print('请把本窗口显示的步骤和错误发来；请勿连续重复安装。')
finally:
    tty_input('\n按回车关闭窗口…')
