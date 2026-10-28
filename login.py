#!/usr/bin/env python3
"""GLaDOS 登录助手：用邮箱 + 密码换一份新 Cookie。

解决两件事:
  1. 忘了 GLaDOS 用的是哪个邮箱 —— 登录成功后脚本会显示账号邮箱，试几个候选即可确认
  2. Cookie 过期 —— 直接拿到新的 Cookie 串，粘到 GitHub Secret 即可

用法:
    python3 login.py                         # 交互式输入邮箱与密码（密码不回显）
    python3 login.py --email a@b.com         # 只给邮箱，密码交互输入
    GLADOS_EMAIL=a@b.com GLADOS_PASSWORD=pw python3 login.py

抓到的 Cookie 只打印在终端，不会写入任何文件；请自行粘贴到仓库 Secret。
"""

import argparse
import getpass
import os
import sys

import requests

from checkin import API, Config

DOMAIN = os.environ.get("GLADOS_LOGIN_DOMAIN", "glados.cloud")
COOKIE_ORDER = ("koa:sess", "koa:sess.sig", "gld:sess", "gld:sess.sig")

"""登录字段名先按最可能的来，服务端不认再换下一组"""
FIELD_VARIANTS = (
    ("email", "password"),
    ("mail", "password"),
    ("username", "password"),
)


def attempt_login(session: requests.Session, email: str, password: str, field_names) -> dict:
    """用给定字段名打一次登录接口"""
    body = {field_names[0]: email, field_names[1]: password}
    try:
        response = session.post(f"https://{DOMAIN}/api/login", json=body, timeout=(10, 30))
    except requests.exceptions.RequestException as error:
        return {"code": None, "message": f"网络错误: {error}"}
    try:
        payload = response.json()
    except ValueError:
        return {"code": None, "message": f"响应不是 JSON (HTTP {response.status_code}): {response.text[:200]}"}
    payload["_http"] = response.status_code
    return payload


def cookie_header(session: requests.Session) -> str:
    """按 GLaDOS 的字段顺序拼出可直接使用的 Cookie 串"""
    jar = session.cookies.get_dict()
    ordered = [name for name in COOKIE_ORDER if name in jar]
    ordered += [name for name in jar if name not in COOKIE_ORDER]
    return "; ".join(f"{name}={jar[name]}" for name in ordered)


def show_account(cookie: str) -> None:
    """用新 Cookie 读一次账号状态，把邮箱等关键信息显示出来"""
    api = API(DOMAIN, verbose=False, user_agent=API.USER_AGENTS["Linux"])
    try:
        data = api._request_json(api._get_full_url(api.STATUS_URL), "GET", None, cookie)
    finally:
        api.close()

    if not isinstance(data, dict) or data.get("code") != 0:
        print(f"  状态查询未通过: {data}")
        return

    info = data.get("data") or {}
    print(f"  邮箱     : {info.get('email') or '（响应中无 email 字段）'}")
    for key in ("vip", "leftDays", "unpaid", "port", "configureId"):
        if info.get(key) is not None:
            print(f"  {key:<9}: {info[key]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="用邮箱和密码换取 GLaDOS 的新 Cookie")
    parser.add_argument("--email", default=os.environ.get("GLADOS_EMAIL", ""), help="GLaDOS 账号邮箱")
    parser.add_argument("--password", default=os.environ.get("GLADOS_PASSWORD", ""), help="账号密码（建议改用交互输入）")
    args = parser.parse_args()

    email = args.email or input("GLaDOS 邮箱: ").strip()
    password = args.password or getpass.getpass("GLaDOS 密码（不回显）: ")
    if not email or not password:
        print("邮箱或密码为空，已退出。")
        return 2

    session = requests.Session()
    session.headers.update({
        "user-agent": API.USER_AGENTS["Linux"],
        "content-type": "application/json;charset=UTF-8",
        "origin": f"https://{DOMAIN}",
        "referer": f"https://{DOMAIN}/login",
    })

    print(f"\n目标站点: {DOMAIN}\n")
    for field_names in FIELD_VARIANTS:
        payload = attempt_login(session, email, password, field_names)
        code = payload.get("code")
        label = f"{field_names[0]}+{field_names[1]}"
        if code == 0:
            print(f"[成功] 字段组合 {label}: {payload.get('message', '')}")
            break
        print(f"[失败] 字段组合 {label}: code={code} {payload.get('message', payload)}")
    else:
        print("\n三种字段组合都未登录成功。请确认邮箱是否正确（可换一个候选邮箱重试）、密码是否变更。")
        return 1

    cookie = cookie_header(session)
    if not cookie:
        print("\n登录返回成功但没拿到任何 Cookie，请把完整响应发给开发者：")
        print(f"  {payload}")
        return 1

    print("\n========== 新 Cookie（粘到仓库 Secret: GLADOS_COOKIES） ==========")
    print(cookie)
    print("==================================================================")
    print(f"长度 {len(cookie)} | 指纹 {Config._cookie_fingerprint(cookie)} | 字段 [{', '.join(Config._cookie_fields(cookie))}]")
    print("（指纹可与 Actions 日志里的 Cookie #1 指纹逐字比对）\n")

    print("账号信息:")
    show_account(cookie)
    return 0


if __name__ == "__main__":
    sys.exit(main())
