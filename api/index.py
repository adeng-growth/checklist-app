#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中小企业增长自检清单 - Vercel Flask Serverless 入口
超简化稳定版
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
            # 简单重定向
            html = '<meta http-equiv="refresh" content="0;url=/admin">'
            resp = Response(html)
            resp.set_cookie('ad_auth', '1')
            return resp
        else:
            return '<p>密码错误</p><a href="/admin/login">返回</a>'

    # GET - 显示登录表单
    html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>登录</title></head>
<body style="font-family:sans-serif;padding:50px">
<h2>后台登录</h2>
<form method="POST">
  <input type="password" name="password" placeholder="密码" required>
  <button type="submit">登录</button>
</form>
</body></html>'''
    return Response(html, mimetype='text/html')


@app.route('/admin')
def admin():
    """后台页面"""
    if not flask_request.cookies.get('ad_auth') == '1':
        return Response('<meta http-equiv="refresh" content="0;url=/admin/login">')

    html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>后台</title></head>
<body style="font-family:sans-serif;padding:20px">
<h2>提交记录</h2>
<a href="/api/export/csv">导出CSV</a> |
<a href="/admin/logout">退出</a>
<div id="data">加载中...</div>
<script>
fetch('/api/records').then(r=>r.json()).then(d=>{
  let html = '<table border="1" cellpadding="8" style="border-collapse:collapse;width:100%">';
  html += '<tr><th>姓名</th><th>公司</th><th>总分</th><th>类型</th></tr>';
  (d.records||[]).forEach(r=>{
    html += '<tr><td>'+r.name+'</td><td>'+r.company+'</td><td>'+r.score_total+'</td><td>'+r.result_type+'</td></tr>';
  });
  html += '</table>';
  document.getElementById('data').innerHTML = html;
});
</script>
</body></html>'''
    return Response(html, mimetype='text/html')


@app.route('/admin/logout')
def logout():
    """退出登录"""
    resp = Response('<meta http-equiv="refresh" content="0;url=/admin/login">')
    resp.set_cookie('ad_auth', '', expires=0)
    return resp


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
        except Exception:
            pass

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
