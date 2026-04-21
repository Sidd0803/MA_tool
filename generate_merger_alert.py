#!/usr/bin/env python3
"""
Merger Live Alert HTML Generator
Generates branded WallachBeth Capital merger alert emails.

Usage:
    python generate_merger_alert.py
    python generate_merger_alert.py --output my_deal.html
    python generate_merger_alert.py --json deal_data.json
"""

import argparse
import json
import os
from datetime import datetime


# ─────────────────────────────────────────────
#  DATA INPUT
# ─────────────────────────────────────────────

def prompt_for_deal() -> dict:
    """Interactively prompt the user for deal details."""
    print("\n" + "="*55)
    print("  WallachBeth Capital — Merger Alert Generator")
    print("="*55 + "\n")

    def ask(label, required=True, default=None):
        prompt = f"  {label}"
        if default:
            prompt += f" [{default}]"
        prompt += ": "
        while True:
            val = input(prompt).strip()
            if val:
                return val
            if default:
                return default
            if not required:
                return ""
            print(f"  ⚠  {label} is required.")

    def ask_multiline(label):
        print(f"\n  {label} (press Enter twice to finish):")
        lines = []
        while True:
            line = input("  > ")
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        return "\n".join(l for l in lines if l)

    # ── Target company ──
    print("── TARGET COMPANY ─────────────────────────────────")
    target_name   = ask("Company Name (e.g. Globalstar)")
    target_ticker = ask("Ticker Symbol (e.g. GSAT)")
    target_exchange = ask("Exchange (e.g. NYSE)", default="NYSE")
    target_ir_url = ask("Investor Relations URL", required=False)

    # ── Acquirer ──
    print("\n── ACQUIRER ────────────────────────────────────────")
    acquirer_name   = ask("Company Name (e.g. Amazon)")
    acquirer_ticker = ask("Ticker Symbol (e.g. AMZN)")
    acquirer_ir_url = ask("Investor Relations URL", required=False)

    # ── Deal stats ──
    print("\n── DEAL STATS ──────────────────────────────────────")
    deal_value        = ask("Deal Value (e.g. $11.68B)")
    per_share_value   = ask("Per Share Value (e.g. $90.00)")
    undisturbed_price = ask("Undisturbed Price (e.g. $41.54)")
    premium_1day      = ask("Premium (1-Day) e.g. 105.93%")
    premium_30day     = ask("Premium (30-Day Avg) e.g. 40.96%")
    expected_close    = ask("Expected Close (e.g. Q4 2027 or 2027)")

    # ── Consideration structure ──
    print("\n── CONSIDERATION STRUCTURE ─────────────────────────")
    print("  Describe the deal structure / exchange ratio.")
    consideration = ask_multiline("Consideration Details")

    # ── Merger narrative ──
    print("\n── MERGER NARRATIVE ────────────────────────────────")
    print("  Full deal description for the email body.")
    narrative_paragraphs_raw = ask_multiline("Narrative (separate paragraphs with blank line)")
    narratives = [p.strip() for p in narrative_paragraphs_raw.split("\n") if p.strip()]

    # ── Links ──
    print("\n── LINKS ───────────────────────────────────────────")
    press_release_url = ask("Press Release URL", required=False)

    # ── Date ──
    alert_date = ask("Alert Date", default=datetime.today().strftime("%B %d, %Y"))

    return {
        "target": {
            "name": target_name,
            "ticker": target_ticker,
            "exchange": target_exchange,
            "ir_url": target_ir_url,
        },
        "acquirer": {
            "name": acquirer_name,
            "ticker": acquirer_ticker,
            "ir_url": acquirer_ir_url,
        },
        "stats": {
            "deal_value": deal_value,
            "per_share_value": per_share_value,
            "undisturbed_price": undisturbed_price,
            "premium_1day": premium_1day,
            "premium_30day": premium_30day,
            "expected_close": expected_close,
        },
        "merger_details": {
            "consideration": consideration,
            "narratives": narratives,
            "press_release_url": press_release_url,
        },
        "alert_date": alert_date,
    }


# ─────────────────────────────────────────────
#  HTML GENERATION
# ─────────────────────────────────────────────

def build_narrative_paragraphs(paragraphs: list[str]) -> str:
    if not paragraphs:
        return ""
    html_parts = []
    for i, para in enumerate(paragraphs):
        margin = "0 0 12px 0" if i < len(paragraphs) - 1 else "0"
        html_parts.append(
            f'<p style="font-size:11px;color:#3D3D3D;line-height:1.7;margin:{margin};">'
            f'{para}</p>'
        )
    return "\n      ".join(html_parts)


def build_links_row(press_release_url, target_ir_url, acquirer_name, acquirer_ir_url, target_name) -> str:
    links = []
    if press_release_url:
        links.append(f'<a href="{press_release_url}" style="color:#08519C;text-decoration:underline;">Press Release</a>')
    if target_ir_url:
        links.append(f'<a href="{target_ir_url}" style="color:#08519C;text-decoration:underline;">{target_name} Investor Relations</a>')
    if acquirer_ir_url:
        links.append(f'<a href="{acquirer_ir_url}" style="color:#08519C;text-decoration:underline;">{acquirer_name} Investor Relations</a>')
    if not links:
        return ""
    separator = "\n        &nbsp;&nbsp;&middot;&nbsp;&nbsp;\n        "
    return (
        f'\n      <p style="font-size:11px;color:#3D3D3D;line-height:1.7;margin:12px 0 0 0;">\n'
        f'        {separator.join(links)}\n'
        f'      </p>'
    )


def generate_html(deal: dict) -> str:
    t  = deal["target"]
    a  = deal["acquirer"]
    s  = deal["stats"]
    md = deal["merger_details"]

    narrative_html = build_narrative_paragraphs(md.get("narratives", []))
    links_html     = build_links_row(
        md.get("press_release_url", ""),
        t.get("ir_url", ""),
        a["name"],
        a.get("ir_url", ""),
        t["name"],
    )
    alert_date = deal.get("alert_date", datetime.today().strftime("%B %d, %Y"))

    # consideration text (may be multi-sentence; escape basic HTML)
    consideration_text = md.get("consideration", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Merger Alert – {t['name']} / {a['name']}</title>
</head>
<body style="margin:0;padding:20px;background:#F0F4F8;font-family:Arial,sans-serif;">

<table width="600" cellpadding="0" cellspacing="0" border="0"
       style="border-collapse:collapse;margin:0 auto;border:1px solid #BDD7EE;">

  <!-- HEADER -->
  <tr>
    <td style="background:#08519C;padding:12px 20px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td>
            <span style="font-size:15px;font-weight:bold;color:#ffffff;letter-spacing:0.5px;">
              WallachBeth Capital
            </span><br/>
            <span style="font-size:10px;color:#DEEBF7;letter-spacing:1px;text-transform:uppercase;">
              Merger Arbitrage Desk
            </span>
          </td>
          <td align="right">
            <span style="font-size:10px;color:#DEEBF7;">{alert_date}</span>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ALERT BADGE -->
  <tr>
    <td style="background:#DEEBF7;padding:6px 20px;">
      <span style="font-size:10px;font-weight:bold;color:#08519C;letter-spacing:1.5px;text-transform:uppercase;">
        &#9679; MERGER LIVE ALERT
      </span>
    </td>
  </tr>

  <!-- DEAL TITLE -->
  <tr>
    <td style="background:#ffffff;padding:16px 20px 12px 20px;">
      <p style="font-size:18px;font-weight:bold;color:#08519C;margin:0 0 4px 0;">
        {t['name']} ({t['exchange']}: {t['ticker']})
      </p>
      <p style="font-size:12px;color:#6B6B6B;margin:0;">
        to be acquired by <strong style="color:#3D3D3D;">{a['name']} ({a['ticker']})</strong>
        &nbsp;&middot;&nbsp; Deal Value: <strong style="color:#3D3D3D;">{s['deal_value']}</strong>
      </p>
    </td>
  </tr>

  <!-- DIVIDER -->
  <tr><td style="background:#DEEBF7;padding:1px 0;"></td></tr>

  <!-- STATS HEADER -->
  <tr>
    <td style="background:#08519C;padding:6px 20px;">
      <span style="font-size:10px;font-weight:bold;color:#DEEBF7;letter-spacing:1px;text-transform:uppercase;">
        Deal Statistics
      </span>
    </td>
  </tr>

  <!-- STATS TABLE -->
  <tr>
    <td style="background:#EFF6FC;padding:12px 20px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">

        <tr>
          <td style="font-size:11px;color:#6B6B6B;padding:8px 0 4px 0;width:50%;vertical-align:top;">
            Acquirer
          </td>
          <td style="font-size:11px;color:#6B6B6B;padding:8px 0 4px 0;width:50%;vertical-align:top;">
            Target
          </td>
        </tr>
        <tr>
          <td style="font-size:13px;font-weight:bold;color:#08519C;padding:0 0 12px 0;">
            {a['name']} ({a['ticker']})
          </td>
          <td style="font-size:13px;font-weight:bold;color:#08519C;padding:0 0 12px 0;">
            {t['name']} ({t['ticker']})
          </td>
        </tr>

        <tr>
          <td colspan="2" style="border-top:1px solid #BDD7EE;padding:0;"></td>
        </tr>

        <tr>
          <td style="font-size:11px;color:#6B6B6B;padding:8px 0 0 0;">Per Share Value</td>
          <td style="font-size:11px;color:#6B6B6B;padding:8px 0 0 0;">Undisturbed Price</td>
        </tr>
        <tr>
          <td style="font-size:13px;font-weight:bold;color:#3D3D3D;padding:2px 0 8px 0;">
            {s['per_share_value']}
          </td>
          <td style="font-size:13px;font-weight:bold;color:#3D3D3D;padding:2px 0 8px 0;">
            {s['undisturbed_price']}
          </td>
        </tr>

        <tr>
          <td colspan="2" style="border-top:1px solid #BDD7EE;padding:0;"></td>
        </tr>

        <tr>
          <td style="font-size:11px;color:#6B6B6B;padding:8px 0 0 0;">Premium (1-Day)</td>
          <td style="font-size:11px;color:#6B6B6B;padding:8px 0 0 0;">Premium (30-Day Avg)</td>
        </tr>
        <tr>
          <td style="font-size:13px;font-weight:bold;color:#3D3D3D;padding:2px 0 8px 0;">
            {s['premium_1day']}
          </td>
          <td style="font-size:13px;font-weight:bold;color:#3D3D3D;padding:2px 0 8px 0;">
            {s['premium_30day']}
          </td>
        </tr>

        <tr>
          <td colspan="2" style="border-top:1px solid #BDD7EE;padding:0;"></td>
        </tr>

        <tr>
          <td style="font-size:11px;color:#6B6B6B;padding:8px 0 0 0;">Expected Close</td>
          <td style="font-size:11px;color:#6B6B6B;padding:8px 0 0 0;">Deal Value</td>
        </tr>
        <tr>
          <td style="font-size:13px;font-weight:bold;color:#3D3D3D;padding:2px 0 8px 0;">
            {s['expected_close']}
          </td>
          <td style="font-size:13px;font-weight:bold;color:#3D3D3D;padding:2px 0 8px 0;">
            {s['deal_value']}
          </td>
        </tr>

      </table>
    </td>
  </tr>

  <!-- DIVIDER -->
  <tr><td style="background:#DEEBF7;padding:1px 0;"></td></tr>

  <!-- CONSIDERATION HEADER -->
  <tr>
    <td style="background:#08519C;padding:6px 20px;">
      <span style="font-size:10px;font-weight:bold;color:#DEEBF7;letter-spacing:1px;text-transform:uppercase;">
        Consideration Structure
      </span>
    </td>
  </tr>

  <!-- CONSIDERATION BODY -->
  <tr>
    <td style="background:#ffffff;padding:14px 20px;">
      <p style="font-size:11px;color:#3D3D3D;line-height:1.7;margin:0;">
        {consideration_text}
      </p>
    </td>
  </tr>

  <!-- DIVIDER -->
  <tr><td style="background:#DEEBF7;padding:1px 0;"></td></tr>

  <!-- NARRATIVE HEADER -->
  <tr>
    <td style="background:#08519C;padding:6px 20px;">
      <span style="font-size:10px;font-weight:bold;color:#DEEBF7;letter-spacing:1px;text-transform:uppercase;">
        Merger Details
      </span>
    </td>
  </tr>

  <!-- NARRATIVE BODY -->
  <tr>
    <td style="background:#ffffff;padding:16px 20px;">
      {narrative_html}{links_html}
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#08519C;padding:8px 20px;text-align:center;">
      <span style="color:#ffffff;font-size:10px;">
        WallachBeth Capital &nbsp;|&nbsp; Confidential &nbsp;|&nbsp; For Internal Use Only
      </span>
    </td>
  </tr>

</table>
</body>
</html>
"""
    return html


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a WallachBeth Merger Live Alert HTML email."
    )
    parser.add_argument(
        "--json", metavar="FILE",
        help="Path to a JSON file with deal data (skips interactive prompts)."
    )
    parser.add_argument(
        "--output", "-o", metavar="FILE", default=None,
        help="Output HTML filename (default: <target_ticker>_merger_alert.html)."
    )
    args = parser.parse_args()

    # Load deal data
    if args.json:
        with open(args.json, "r") as f:
            deal = json.load(f)
        print(f"\n  Loaded deal data from {args.json}")
    else:
        deal = prompt_for_deal()

    # Generate HTML
    html = generate_html(deal)

    # Determine output filename
    output_file = args.output or f"{deal['target']['ticker'].upper()}_merger_alert.html"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  ✅  HTML saved to: {output_file}\n")


if __name__ == "__main__":
    main()
