#!/usr/bin/env python3
"""Reusable Gmail email sender (zero third-party dependencies).

Sends email through the Gmail REST API using OAuth 2.0. An OAuth *refresh
token* (which does not expire) is exchanged for a short-lived access token on
every run, so no manual token pasting is ever required after the one-time
setup.

Credentials are read from environment variables (never hard-coded / committed):

    GMAIL_CLIENT_ID       OAuth client id
    GMAIL_CLIENT_SECRET   OAuth client secret
    GMAIL_REFRESH_TOKEN   OAuth refresh token (long-lived)
    GMAIL_SENDER          (optional) From address; defaults to "me"
    GMAIL_FORCE_IPV4      (optional) set to "1" on IPv6-restricted hosts

Use as a library:

    from scripts.send_email import send_email
    send_email("someone@example.com", "Hi", "Body text")

Use from the command line:

    python scripts/send_email.py --to someone@example.com \
        --subject "Hi" --body "Body text"
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
SEND_ENDPOINT = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


class EmailError(RuntimeError):
    """Raised when sending fails for a non-transient reason."""


def _maybe_force_ipv4() -> None:
    """Force IPv4 resolution when GMAIL_FORCE_IPV4 is set.

    Some sandboxed/cloud hosts cannot create IPv6 sockets; restricting DNS
    results to A records avoids 'Address family not supported' errors.
    """
    if os.environ.get("GMAIL_FORCE_IPV4") != "1":
        return
    _orig = socket.getaddrinfo

    def ipv4_only(host, *args, **kwargs):
        return [r for r in _orig(host, *args, **kwargs) if r[0] == socket.AF_INET]

    socket.getaddrinfo = ipv4_only


def _read_credentials() -> dict:
    missing = [
        name
        for name in ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN")
        if not os.environ.get(name)
    ]
    if missing:
        raise EmailError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". See scripts/README.md for setup."
        )
    return {
        "client_id": os.environ["GMAIL_CLIENT_ID"],
        "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
        "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"],
    }


def get_access_token(creds: dict | None = None) -> str:
    """Exchange the refresh token for a fresh access token."""
    creds = creds or _read_credentials()
    data = urllib.parse.urlencode(
        {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        }
    ).encode()
    req = urllib.request.Request(
        TOKEN_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:  # noqa: PERF203
        body = exc.read().decode(errors="replace")
        raise EmailError(f"Token refresh failed ({exc.code}): {body}") from exc
    token = payload.get("access_token")
    if not token:
        raise EmailError(f"Token refresh returned no access_token: {payload}")
    return token


def _build_raw_message(
    to: list[str],
    subject: str,
    body: str,
    sender: str,
    html_body: str | None,
    cc: list[str] | None,
    bcc: list[str] | None,
) -> str:
    if html_body:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
    else:
        msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = ", ".join(to)
    msg["From"] = sender
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def send_email(
    to: str | list[str],
    subject: str,
    body: str,
    *,
    sender: str | None = None,
    html_body: str | None = None,
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None,
    creds: dict | None = None,
) -> dict:
    """Send an email via the Gmail API. Returns the API response dict.

    `to`, `cc`, `bcc` accept a single address or a list of addresses.
    """
    _maybe_force_ipv4()

    def _as_list(v):
        if v is None:
            return None
        return [v] if isinstance(v, str) else list(v)

    to_list = _as_list(to) or []
    if not to_list:
        raise EmailError("At least one recipient is required.")

    sender = sender or os.environ.get("GMAIL_SENDER") or "me"
    access_token = get_access_token(creds)
    raw = _build_raw_message(
        to_list, subject, body, sender, html_body, _as_list(cc), _as_list(bcc)
    )

    req = urllib.request.Request(
        SEND_ENDPOINT,
        data=json.dumps({"raw": raw}).encode(),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        raise EmailError(f"Send failed ({exc.code}): {body_text}") from exc


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send an email via the Gmail API.")
    parser.add_argument("--to", required=True, action="append",
                        help="Recipient address (repeat for multiple).")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", help="Plain-text body. If omitted, read from stdin.")
    parser.add_argument("--html", help="Optional HTML body.")
    parser.add_argument("--cc", action="append", default=None)
    parser.add_argument("--bcc", action="append", default=None)
    parser.add_argument("--from", dest="sender", help="From address (default: env/me).")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    body = args.body if args.body is not None else sys.stdin.read()
    try:
        result = send_email(
            args.to,
            args.subject,
            body,
            sender=args.sender,
            html_body=args.html,
            cc=args.cc,
            bcc=args.bcc,
        )
    except EmailError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"sent: id={result.get('id')} thread={result.get('threadId')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
