#!/usr/bin/env node
/**
 * send-self.js — Send a Gmail message to yourself via the Gmail API.
 *
 * Why the Gmail API (and not SMTP)?
 *   The remote execution sandbox blocks outbound SMTP (ports 465/587), so
 *   nodemailer / App Password won't work here. Only HTTPS (443) is open, so we
 *   talk to gmail.googleapis.com directly. Token refresh and send both go over
 *   443, which means this works headlessly with no browser.
 *
 * One-time setup (on your own machine) — see scripts/README.md:
 *   You need a Google OAuth client and a refresh token with the
 *   https://www.googleapis.com/auth/gmail.send scope. Provide them as env vars.
 *
 * Required environment variables:
 *   GOOGLE_CLIENT_ID       OAuth 2.0 client ID
 *   GOOGLE_CLIENT_SECRET   OAuth 2.0 client secret
 *   GOOGLE_REFRESH_TOKEN   Refresh token with gmail.send scope
 *
 * Optional environment variables:
 *   MAIL_TO        Recipient (default: a413123a413123@gmail.com)
 *   MAIL_FROM      Sender    (default: same as MAIL_TO)
 *   MAIL_SUBJECT   Subject   (default: "StudyZen test mail")
 *   MAIL_BODY      Body text (default: a short test message)
 *
 * Usage:
 *   node scripts/send-self.js
 *   MAIL_SUBJECT="Hello" MAIL_BODY="hi" node scripts/send-self.js
 */

'use strict';

const DEFAULT_ADDRESS = 'a413123a413123@gmail.com';

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    console.error(`Missing required environment variable: ${name}`);
    console.error('See scripts/README.md for how to obtain OAuth credentials.');
    process.exit(1);
  }
  return value;
}

/** Exchange a long-lived refresh token for a short-lived access token. */
async function getAccessToken({ clientId, clientSecret, refreshToken }) {
  const res = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: clientId,
      client_secret: clientSecret,
      refresh_token: refreshToken,
      grant_type: 'refresh_token',
    }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(
      `Token refresh failed (${res.status}): ${data.error || ''} ${data.error_description || ''}`.trim()
    );
  }
  return data.access_token;
}

/** Build a raw RFC 2822 message and base64url-encode it for the Gmail API. */
function buildRawMessage({ from, to, subject, body }) {
  const headers = [
    `From: ${from}`,
    `To: ${to}`,
    `Subject: =?UTF-8?B?${Buffer.from(subject, 'utf8').toString('base64')}?=`,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset="UTF-8"',
    'Content-Transfer-Encoding: base64',
  ];
  const encodedBody = Buffer.from(body, 'utf8').toString('base64');
  const message = `${headers.join('\r\n')}\r\n\r\n${encodedBody}`;
  return Buffer.from(message, 'utf8')
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

async function sendMessage(accessToken, raw) {
  const res = await fetch(
    'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ raw }),
    }
  );

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.error ? JSON.stringify(data.error) : `HTTP ${res.status}`;
    throw new Error(`Send failed: ${detail}`);
  }
  return data;
}

async function main() {
  const credentials = {
    clientId: requireEnv('GOOGLE_CLIENT_ID'),
    clientSecret: requireEnv('GOOGLE_CLIENT_SECRET'),
    refreshToken: requireEnv('GOOGLE_REFRESH_TOKEN'),
  };

  const to = process.env.MAIL_TO || DEFAULT_ADDRESS;
  const from = process.env.MAIL_FROM || to;
  const subject = process.env.MAIL_SUBJECT || 'StudyZen test mail';
  const body =
    process.env.MAIL_BODY ||
    `This is a test message sent to yourself via the Gmail API.\nSent at ${new Date().toISOString()}`;

  console.log(`Requesting access token...`);
  const accessToken = await getAccessToken(credentials);

  console.log(`Sending mail to ${to} ...`);
  const raw = buildRawMessage({ from, to, subject, body });
  const result = await sendMessage(accessToken, raw);

  console.log(`Sent. Message id: ${result.id}`);
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
