"""
Bluestock MF Capstone — Automated HTML Email Report (B5 bonus)

Generates and optionally emails a weekly MF performance summary.

Usage:
    python scripts/email_report.py                    # Preview only (stdout)
    python scripts/email_report.py --send recipient@example.com

Cron (weekly Monday 9 AM):
    0 9 * * 1 /usr/bin/python3 /path/to/scripts/email_report.py --send user@example.com
"""

import argparse
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd
from jinja2 import Template

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
REPORTS = BASE / "reports"

TEMPLATE_STR = """
<html><body>
  <h2>Bluestock MF — Weekly Performance Summary</h2>
  <p>Week ending: {{ report_date }}</p>
  <h3>Top 5 Funds by 1-Week Return</h3>
  {{ table_html }}
  <hr>
  <p><small>Generated automatically by Bluestock MF Analytics Pipeline</small></p>
</body></html>
"""


def generate_html() -> str:
    scorecard_path = REPORTS / "fund_scorecard.csv"
    if not scorecard_path.exists():
        log.warning("fund_scorecard.csv not found; using fallback data")
        df = pd.DataFrame({"Scheme": ["N/A"], "Score": [0]})
    else:
        df = pd.read_csv(scorecard_path).head(5)
    table_html = df.to_html(index=False, border=0)
    template = Template(TEMPLATE_STR)
    return template.render(
        report_date=pd.Timestamp.today().strftime("%d %b %Y"),
        table_html=table_html,
    )


def send_email(recipient: str, html_body: str, smtp_server: str = "localhost", port: int = 25):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Bluestock MF Weekly Report — {pd.Timestamp.today().strftime('%d %b %Y')}"
    msg["From"] = "noreply@bluestock-mf.com"
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP(smtp_server, port) as server:
        server.send_message(msg)
    log.info("Email sent to %s", recipient)


def main():
    parser = argparse.ArgumentParser(description="Generate and send weekly MF email report")
    parser.add_argument("--send", type=str, help="Recipient email address")
    args = parser.parse_args()

    html = generate_html()

    if args.send:
        try:
            send_email(args.send, html)
            print(f"Weekly report sent to {args.send}")
        except Exception as e:
            log.error("Failed to send email: %s", e)
            print(html)
    else:
        print(html)


if __name__ == "__main__":
    main()
