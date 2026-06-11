# Gmail 寄信模組（`send_email.py`）

一個**零第三方相依套件**（純 Python 標準庫）的 Gmail 寄信工具，透過 Gmail
REST API 寄送郵件。使用 OAuth **refresh token** 自動換取短效 access token，
**設定一次之後就不用再手動貼 token**。

## 為什麼用 refresh token？

- `access token`：1 小時就過期，不適合長期重複使用。
- `refresh token`：長期有效，程式每次寄信前用它自動換一個新的 access token。

憑證一律放在**環境變數**，不寫死在程式碼、也不進 git。

## 一次性設定

### 1. 取得 OAuth 憑證與 refresh token

最快的方式是用 [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)：

1. 右上角齒輪 ⚙️ → 勾選 **Use your own OAuth credentials**，填入你的
   `Client ID` / `Client secret`（在 [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   建立 OAuth client，類型選 Web，redirect URI 加
   `https://developers.google.com/oauthplayground`）。
2. 左側 **Step 1** 的 scope 欄輸入：`https://www.googleapis.com/auth/gmail.send`
3. **Authorize APIs** → 登入並授權。
4. **Step 2** → **Exchange authorization code for tokens**。
5. 複製 **Refresh token**（這個就是要長期保存的那個）。

### 2. 設定環境變數

```bash
export GMAIL_CLIENT_ID="你的 client id"
export GMAIL_CLIENT_SECRET="你的 client secret"
export GMAIL_REFRESH_TOKEN="你的 refresh token"
export GMAIL_SENDER="你的@gmail.com"   # 選填，預設為 "me"
# 在封鎖 IPv6 的雲端環境才需要：
# export GMAIL_FORCE_IPV4=1
```

可複製 `.env.example` 成 `.env` 後填值（`.env` 已被 `.gitignore` 忽略）。

## 使用方式

### 命令列

```bash
python scripts/send_email.py \
  --to someone@example.com \
  --subject "測試信" \
  --body "這是一封測試用的郵件。"
```

其他選項：`--html`、`--cc`、`--bcc`、`--from`，`--to/--cc/--bcc` 可重複指定多個收件人。
不給 `--body` 時會從 stdin 讀取內文。

### 當作函式庫

```python
from scripts.send_email import send_email

send_email(
    to="someone@example.com",
    subject="測試信",
    body="純文字內容",
    html_body="<b>HTML 內容</b>",   # 選填
)
```

## 需要的 OAuth scope

`https://www.googleapis.com/auth/gmail.send` —— 只有「寄信」權限，無法讀取信件，風險最小化。
