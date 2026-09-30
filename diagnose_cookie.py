#!/usr/bin/env python3
"""GLaDOS Cookie 本地诊断：只读探测，判断 Cookie 是否有效、属于哪个域名。

用法:
    python3 diagnose_cookie.py "koa:sess=...; koa:sess.sig=..."
    GLADOS_COOKIES="..." python3 diagnose_cookie.py
    GLADOS_DOMAINS="glados.cloud,railgun.info" python3 diagnose_cookie.py "..."

多账号用 & 或换行分隔，折行粘贴会自动还原。只请求 /api/user/status，不会触发签到。
Cookie 解析直接复用 checkin.py，保证与签到脚本的判定一致；指纹为 sha256 前 12 位，
可与 Actions 日志逐字比对。
"""

import os
import sys

import requests

from checkin import Config

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"


def probe_status(domain: str, cookie: str) -> dict:
    """只读探测某个域名是否认可该 Cookie"""
    headers = {
        "cookie": cookie,
        "referer": f"https://{domain}/console/checkin",
        "origin": f"https://{domain}",
        "user-agent": USER_AGENT,
        "content-type": "application/json;charset=UTF-8",
    }
    try:
        response = requests.get(f"https://{domain}/api/user/status", headers=headers, timeout=(10, 30))
    except requests.exceptions.RequestException as error:
        return {"error": str(error)}
    try:
        data = response.json()
    except ValueError:
        return {"http": response.status_code, "error": f"响应不是 JSON: {response.text[:200]}"}
    return {"http": response.status_code, "data": data}


def main() -> int:
    raw = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(Config.ENV_COOKIES, "")
    if not raw.strip():
        print(f'用法: python3 diagnose_cookie.py "<cookie>"  或先设置环境变量 {Config.ENV_COOKIES}')
        return 2

    domains = Config._parse_domains(os.environ.get(Config.ENV_DOMAINS, "")) or list(Config.DOMAINS)
    cookies = Config._split_cookies(raw)
    print(f"共 {len(cookies)} 个 Cookie，探测 {len(domains)} 个域名: {', '.join(domains)}\n")

    authed_cookies = []
    for index, cookie in enumerate(cookies, 1):
        fields = Config._cookie_fields(cookie)
        print(f"--- Cookie #{index} | 长度 {len(cookie)} | 指纹 {Config._cookie_fingerprint(cookie)} | 字段 [{', '.join(fields)}]")

        missing = [field for field in Config.REQUIRED_COOKIE_FIELDS if field not in fields]
        if missing:
            print(f"    [!] 缺少字段 {missing} -> 结构不完整，必然鉴权失败")

        authed = []
        for domain in domains:
            result = probe_status(domain, cookie)
            if "error" in result:
                print(f"    {domain:<16} HTTP={result.get('http', '-')} 请求异常: {result['error']}")
                continue
            data = result.get("data") or {}
            code = data.get("code")
            if code == 0:
                left_days = (data.get("data") or {}).get("leftDays")
                authed.append(domain)
                print(f"    {domain:<16} HTTP={result['http']} code=0  [通过鉴权] leftDays={left_days}")
            else:
                print(f"    {domain:<16} HTTP={result['http']} code={code}  {data.get('message', data)}")

        if authed:
            authed_cookies.append((index, authed))
            print(f"    => Cookie #{index} 有效，属于: {', '.join(authed)}")
        else:
            print(f"    => Cookie #{index} 未通过任何域名的鉴权")
        print()

    print("========== 结论 ==========")
    if not authed_cookies:
        print("所有 Cookie 在所有域名上均返回 -2 未授权。")
        print("与『完全不发送 Cookie』的响应完全一致 => 该 Cookie 已失效或字段残缺。")
        print("处理: 重新登录 GLaDOS -> 签到页面按 F12 -> Network -> 复制请求头里的完整 Cookie (含 koa:sess 与 koa:sess.sig) -> 更新 GitHub Secret。")
        return 1

    for index, authed in authed_cookies:
        print(f"Cookie #{index}: 服务端认可，域名 {', '.join(authed)}。")
    print("若 Actions 仍失败: 核对日志里的 Cookie 指纹是否与此处一致，不一致说明 Secret 没更新成功。")
    print(f"Cookie 不属于的域名会被自动标记为『域名不适用』而不计入失败；也可用 {Config.ENV_DOMAINS} 显式指定域名。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
