# Glados自动签到

## 食用方式：

### 注册一个GLaDOS的账号([注册地址](https://glados.space/landing/0A58E-NV28S-6U3QV-33VMG))

#### 我的邀请码：([0A58E-NV28S-6U3QV-33VMG](https://0a58e-nv28s-6u3qv-33vmg.glados.space)) 

#### 我的优惠码（9折）：([DEVILSTORE](https://0a58e-nv28s-6u3qv-33vmg.glados.space)) 

### **Fork**本仓库

![图片加载失败](imgs/1.png)

### 添加**secret**

1. 跳转至自己的仓库的`Settings`->`Secrets and variables`->`Action`

2. 添加1个`repository secret`，命名为`GLADOS_COOKIES`，其值对应GLaDOS账号的cookie值中的有效部分（获取方式如下）

- 在GLaDOS的签到页面按`F12`

- 切换到`Network`页面下，刷新

![图片加载失败](imgs/2.png)

- 点击第一个选项卡后在`Request Headers`下找到`Cookie`，右键复制cookie的值即可

  > 参考格式：koa:sess=eyJ1c2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxAwMH0=; koa:sess.sig=xJkOxxxxxxxxxxxxxxxtnM;

![图片加载失败](imgs/3.png)

- 多账号请在 `COOKIES` 中添加多个 `cookies`，用 `&` 或换行分隔均可（例如 `c1&c2`，或一行一个）。粘贴时折行、误带 `cookie:` 头名、重复粘贴同一份，脚本都会自动还原与去重。

> `glados.cloud` / `glados.space` / `glados.network` 是**同一个账号与积分池**的三个入口：脚本只会签到一次、只会兑换一次，其余入口标记为「同账号已签到」跳过，不会重复消耗积分。`railgun.info` 是独立站点，需要它自己的 Cookie。
>
> 若 Cookie 属于以上之外的站点，可用 `GLADOS_DOMAINS` secret（逗号分隔）显式指定，例如 `glados.cloud,railgun.info`。

3. 配置积分兑换策略（非必须）

- 添加1个`repository secret`，命名为`GLADOS_EXCHANGE_PLAN`，配置自动兑换积分策略：

| 值 | 积分要求 | 兑换天数 |
|---|---------|---------|
| `plan100` | 100 积分 | 10 天 |
| `plan200` | 200 积分 | 30 天 |
| `plan500` | 500 积分 | 100 天 (默认) |

> 不配置时默认为 `plan500`，即积分达到 500 时自动兑换 100 天

4. 手机推送（非必须）

- 添加1个`repository secret`，命名为`PUSHDEER_SENDKEY`，其值对应 PushDeer key: ([获取地址](https://www.pushdeer.com/product.html))。

### **star**自己的仓库

![图片加载失败](imgs/4.png)

## 文件结构

```shell
│  checkin.py	# 签到脚本
│  diagnose_cookie.py	# Cookie 本地诊断（判断 Cookie 是否失效、属于哪个域名）
│
├─.github
│  └─workflows
│          gladosCheck.yml	# Actions 配置文件
```

## 更新日志

- **2026-01**: 重构代码，添加log输出方便定位，支持新版网址，支持配置积分兑换策略。
- **2026-04**: 优化代码逻辑，优化日志输出，支持[新版域名](https://railgun.info) ，在 GLADOS_COOKIES 中添加新版域名下的 cookies 即可使用。
- **2026-09**: 默认域名扩展至 glados.cloud / glados.space / glados.network / railgun.info（可用 `GLADOS_DOMAINS` 覆盖）；Cookie 解析容忍折行、`cookie:` 头名与重复粘贴；同一账号只签到一次、只兑换一次；未通过鉴权的域名直接跳过，不再空发签到/积分/兑换请求；签到遇到 `device-mismatch`（登录设备与请求设备平台不一致）时自动切换同平台 UA 重试一次（可用 `GLADOS_USER_AGENT` 指定）；日志增加 Cookie 指纹用于核对 Secret 是否为最新；新增 `diagnose_cookie.py`。


## 问题排查与定位
- 大家可以通过查询 actions 中的 running checkin 日志快速定位问题，有其他问题提交issue。

  <img width="1684" height="844" alt="image" src="https://github.com/user-attachments/assets/45348a5f-43e4-45f5-8fdf-ce84d343b30d" />

- 日志出现 `code : -2 / 没有权限 / No permission`：服务端判定未登录。这与完全不发送 Cookie 的响应一模一样，说明 Cookie 已失效或字段残缺（缺 `koa:sess` / `koa:sess.sig`），重新登录后获取最新 Cookie 更新 Secret 即可。
- 日志出现 `code : 4 / Automated check-in detected / reason : device-mismatch`：签到接口在比对「登录设备」与「请求设备」的平台。脚本会读取响应里的 `loginDevice`，自动切成同平台 UA 重试一次；想省掉这次重试，可用 `GLADOS_USER_AGENT` secret 直接指定与登录设备一致的 UA（Linux Chrome 示例：`Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36`）。
- 日志里的 `Cookie #N: 长度 …, 指纹 …, 字段 [...]` 用于核对本次运行实际用的是不是刚更新的 Secret：把同一 Cookie 喂给本地诊断脚本，指纹应当一致。
- 本地诊断（只读，不触发签到）。Actions 签到失败时也会自动执行这一步，结果直接打印在日志末尾：

  ```shell
  python diagnose_cookie.py "koa:sess=...; koa:sess.sig=..."
  # 或
  GLADOS_COOKIES="..." python diagnose_cookie.py
  ```

## 声明

本项目不保证稳定运行与更新, 因GitHub相关规定可能会删库, 请注意备份







