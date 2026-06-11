# Send Gmail to yourself (`send-self.js`)

Sends an email **from your Gmail account to yourself** using the **Gmail API**.

## Why the Gmail API and not SMTP?

This script is meant to run inside the Claude Code remote sandbox, where:

- Outbound **SMTP is blocked** (ports 465 and 587) — so App Password + `nodemailer`
  does **not** work.
- Only **HTTPS (443)** is open, and `gmail.googleapis.com` is reachable.

The Gmail API does both the token refresh and the send over 443, so it works
headlessly with no browser once you have a refresh token.

## One-time setup (do this on your own machine, with a browser)

You need three values: a **client ID**, **client secret**, and a **refresh token**
with the `gmail.send` scope.

### 1. Create a Google OAuth client

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project (or pick an existing one).
3. **APIs & Services → Library** → search **Gmail API** → **Enable**.
4. **APIs & Services → OAuth consent screen**:
   - User type: **External**.
   - Fill in the required app name / email fields.
   - Under **Test users**, add `a413123a413123@gmail.com`.
5. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Web application**.
   - Under **Authorized redirect URIs**, add:
     `https://developers.google.com/oauthplayground`
   - Save, then copy the **Client ID** and **Client secret**.

### 2. Get a refresh token via OAuth Playground

1. Open the [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/).
2. Click the **gear icon** (top right) → check **Use your own OAuth credentials**
   → paste your **Client ID** and **Client secret**.
3. In the left **Step 1** box, paste this scope:
   `https://www.googleapis.com/auth/gmail.send`
4. Click **Authorize APIs**, sign in as `a413123a413123@gmail.com`, and allow.
   (You may see an "unverified app" warning — continue, since you added yourself
   as a test user.)
5. In **Step 2**, click **Exchange authorization code for tokens**.
6. Copy the **Refresh token** value.

### 3. Provide the credentials as environment variables

Set these in the remote environment (or export them before running locally):

| Variable               | Value                      |
| ---------------------- | -------------------------- |
| `GOOGLE_CLIENT_ID`     | OAuth client ID            |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret        |
| `GOOGLE_REFRESH_TOKEN` | Refresh token from step 2  |

> Keep these secret — do **not** commit them. The script reads them from the
> environment only.

## Run

```bash
node scripts/send-self.js
```

Override any of the message fields:

```bash
MAIL_SUBJECT="Hello" MAIL_BODY="hi from the sandbox" node scripts/send-self.js
```

### Environment variables reference

| Variable       | Required | Default                     |
| -------------- | -------- | --------------------------- |
| `GOOGLE_CLIENT_ID`     | yes | —                    |
| `GOOGLE_CLIENT_SECRET` | yes | —                    |
| `GOOGLE_REFRESH_TOKEN` | yes | —                    |
| `MAIL_TO`      | no       | `a413123a413123@gmail.com`  |
| `MAIL_FROM`    | no       | same as `MAIL_TO`           |
| `MAIL_SUBJECT` | no       | `StudyZen test mail`        |
| `MAIL_BODY`    | no       | short timestamped message   |

## Requirements

Node.js 18+ (uses the built-in global `fetch`). No npm packages needed.
