#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中小企业增长自检清单 - Vercel Flask Serverless 入口
增强版 v2 - 逐步恢复功能
"""

import os
import json
import requests as req_lib
from flask import Flask, request as flask_request, Response

# ===== Flask App =====
app = Flask(__name__)

# ===== 配置 =====
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY', '')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID', '')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'adeng2026')

# ===== HTML 模板 =====
LOGIN_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>后台登录</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:linear-gradient(135deg,#1a365d,#2d5a87);min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#fff;padding:40px 36px;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.3);width:92%;max-width:380px}
h2{font-size:22px;color:#1a365d;margin-bottom:8px;text-align:center}
.sub{font-size:13px;color:#999;margin-bottom:28px;text-align:center}
.err{background:#ffebee;color:#c62828;padding:10px 16px;border-radius:8px;margin-bottom:16px;font-size:13px;text-align:center}
input{width:100%;padding:12px 16px;border:1.5px solid #e5e5e5;border-radius:10px;font-size:15px;outline:none;transition:border .2s;margin-bottom:20px}
input:focus{border-color:#2d5a87}
button{width:100%;padding:14px;background:linear-gradient(135deg,#1a365d,#2d5a87);color:#fff;border:none;border-radius:10px;font-size:16px;font-weight:600;cursor:pointer;transition:transform .15s}
button:active{transform:scale(.97)}
.ft{font-size:11px;color:#ccc;text-align:center;margin-top:20px}
</style></head>
<body>
<div class="box">
  <h2>&#128274; 后台登录</h2>
  <p class="sub">中小企业增长自检清单</p>
  {{ERROR}}
  <form method="POST"><input type="password" name="password" placeholder="请输入后台密码" required autofocus>
  <button type="submit">登 录</button></form>
  <p class="ft">ADENG CHECKLIST 2026</p>
</div></body></html>'''

ADMIN_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>管理后台</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f7fa}
.top{background:linear-gradient(135deg,#1a365d,#2d5a87);color:#fff;padding:16px 24px;display:flex;justify-content:space-between;align-items:center}
.top h1{font-size:18px}
.top a{color:#fff;text-decoration:none;font-size:13px;background:rgba(255,255,255,.2);padding:6px 14px;border-radius:8px}
.container{max-width:1100px;margin:24px auto;padding:0 16px}
.card{background:#fff;border-radius:16px;padding:24px;box-shadow:0 2px 12px rgba(0,0,0,.08);margin-bottom:20px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f0f4f8;padding:10px 8px;text-align:center;font-weight:600;color:#1a365d;border-bottom:2px solid #e5e5e5}
td{padding:10px 8px;text-align:center;border-bottom:1px solid #f0f0f0}
tr:hover{background:#f8fafc}
</style></head>
<body>
<div class="top"><h1>&#128218; 提交记录</h1><div><a href="/api/export/csv">导出CSV</a><a href="/admin/logout" style="margin-left:8px">退出</a></div></div>
<div class="container">
<div class="card">
  <div id="data">加载中...</div>
</div></div>
<script>
fetch('/api/records').then(r=>r.json()).then(d=>{
  let html = '<table><tr><th>姓名</th><th>公司</th><th>总分</th><th>类型</th></tr>';
  (d.records||[]).forEach(r=>{
    html += '<tr><td>'+r.name+'</td><td>'+r.company+'</td><td>'+r.score_total+'</td><td>'+r.result_type+'</td></tr>';
  });
  html += '</table>';
  document.getElementById('data').innerHTML = html;
});
</script>
</body></html>'''


@app.route('/api/health')
def health():
    """健康检查"""
    return Response(
        json.dumps({'status': 'ok'}),
        mimetype='application/json'
    )


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """登录页面"""
    if flask_request.method == 'POST':
        pw = flask_request.form.get('password', '')
        if pw == ADMIN_PASSWORD:
            html = '<meta http-equiv="refresh" content="0;url=/admin">'
            resp = Response(html)
            resp.set_cookie('ad_auth', '1')
            return resp
        else:
            return Response(
                LOGIN_HTML.replace('{{ERROR}}', '<div class="err">密码错误，请重试</div>'),
                mimetype='text/html'
            )

    # GET - 显示登录表单
    html = LOGIN_HTML.replace('{{ERROR}}', '')
    return Response(html, mimetype='text/html')


@app.route('/admin/logout')
def logout():
    """退出登录"""
    resp = Response('<meta http-equiv="refresh" content="0;url=/admin/login">')
    resp.set_cookie('ad_auth', '', expires=0)
    return resp


@app.route('/admin')
def admin():
    """后台页面"""
    if not flask_request.cookies.get('ad_auth') == '1':
        return Response('<meta http-equiv="refresh" content="0;url=/admin/login">')

    return Response(ADMIN_HTML, mimetype='text/html')


@app.route('/api/records')
def records():
    """获取记录"""
    if not flask_request.cookies.get('ad_auth') == '1':
        return Response(json.dumps({'success': False}), mimetype='application/json')

    if not (AIRTABLE_API_KEY and AIRTABLE_BASE_ID):
        return Response(json.dumps({'records': []}), mimetype='application/json')

    try:
        url = 'https://api.airtable.com/v0/' + AIRTABLE_BASE_ID + '/Submissions'
        headers = {'Authorization': 'Bearer ' + AIRTABLE_API_KEY}
        r = req_lib.get(url, headers=headers, params={'pageSize': 100}, timeout=10)

        if r.status_code != 200:
            return Response(json.dumps({'records': []}), mimetype='application/json')

        recs = []
        for item in r.json().get('records', []):
            f = item.get('fields', {})
            recs.append({
                'name': f.get('Name', ''),
                'company': f.get('Company', ''),
                'score_total': f.get('ScoreTotal', 0),
                'result_type': f.get('ResultType', ''),
            })
        return Response(json.dumps({'records': recs}), mimetype='application/json')
    except Exception as e:
        print('Error:', e)
        return Response(json.dumps({'records': []}), mimetype='application/json')


@app.route('/api/export/csv')
def export_csv():
    """导出CSV"""
    if not flask_request.cookies.get('ad_auth') == '1':
        return Response('Unauthorized', status=401)

    # 读取数据
    rows = []
    if AIRTABLE_API_KEY and AIRTABLE_BASE_ID:
        try:
            url = 'https://api.airtable.com/v0/' + AIRTABLE_BASE_ID + '/Submissions'
            headers = {'Authorization': 'Bearer ' + AIRTABLE_API_KEY}
            r = req_lib.get(url, headers=headers, params={'pageSize': 100}, timeout=10)
            if r.status_code == 200:
                for item in r.json().get('records', []):
                    f = item.get('fields', {})
                    rows.append([
                        f.get('Name', ''),
                        f.get('Company', ''),
                        str(f.get('ScoreTotal', 0)),
                        f.get('ResultType', ''),
                    ])
        except Exception as e:
            print('Export error:', e)

    # 生成CSV
    output = []
    output.append('"姓名","公司","总分","类型"')
    for row in rows:
        formatted = ['"' + str(v).replace('"', '""') + '"' for v in row]
        output.append(','.join(formatted))

    csv_content = '\n'.join(output)
    csv_bytes = csv_content.encode('utf-8-sig')  # BOM for Excel

    resp = Response(csv_bytes, mimetype='text/csv; charset=utf-8')
    resp.headers['Content-Disposition'] = 'attachment; filename="data.csv"'
    return resp


if __name__ == '__main__':
    app.run(debug=True)
