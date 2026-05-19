#!/usr/bin/env python3
"""
WallachBeth Merger Arbitrage HTML Generator (v2 – email-width fix)
--------------------------------------------
Reads a merger arbitrage Excel file and outputs a branded HTML table
showing the 10 most recently announced deals, sorted by date descending.

Usage:
    python generate_MA_html_v2.py <input.xlsx> [output.html]

Arguments:
    input.xlsx    Path to the Excel file (same format as ma_input_sample.xlsx)
    output.html   Optional output path (default: merger_arb.html)

Expected Excel columns (row 1 = header, data from row 2):
    A: Target
    B: Announced Date  (or Track Deals if present — auto-detected and skipped)
    C: Acquirer
    D: Deal Type
    E: Closing Value
    F: Deal Price
    G: Last Price
    H: Pre-Deal Price
    I: Pre-Rumor Price
    J: Target Volume
    K: Options
    L: Div. Yield
    M: Estimated Closing
    N: Return
    O: Annualized Return
"""

import sys
import os
from datetime import datetime, date

try:
    import openpyxl
except ImportError:
    print("Error: openpyxl required.  pip install openpyxl")
    sys.exit(1)

# ── Brand palette ─────────────────────────────────────────────────────────────
BLUE       = "#08519C"
BLUE_LITE  = "#DEEBF7"
STRIPE     = "#F2F7FC"
WHITE      = "#ffffff"
DARK_GRAY  = "#3D3D3D"
MID_GRAY   = "#6B6B6B"
GREEN_BG   = "#e6f4ec"
GREEN_FG   = "#1A7C3E"
RED_BG     = "#fdeaea"
RED_FG     = "#C0392B"

TOP_N      = 10   # number of deals to show


# ── Formatting helpers ────────────────────────────────────────────────────────

def fmt_date(val):
    if isinstance(val, (datetime, date)):
        return val.strftime("%-m/%-d/%y") if sys.platform != "win32" else val.strftime("%#m/%#d/%y")
    return str(val).strip() if val else "—"


def fmt_pct(val):
    """Format a decimal like 0.0161 → '1.61%', with sign preserved."""
    if val is None or val == "N/A" or str(val).strip() == "":
        return "—"
    try:
        f = float(val)
        return f"{f * 100:.2f}%"
    except (ValueError, TypeError):
        return str(val).strip()


def fmt_number(val):
    if val is None:
        return "—"
    try:
        return f"{int(float(str(val).replace(',', ''))):,}"
    except (ValueError, TypeError):
        s = str(val).strip()
        return s if s else "—"


def fmt_price(val):
    if val is None:
        return "—"
    try:
        return f"${float(val):,.2f}"
    except (ValueError, TypeError):
        s = str(val).strip()
        return s if s else "—"


def fmt_yield(val):
    if val is None or str(val).strip() in ("", "N/A", "nan"):
        return "—"
    try:
        return f"{float(val) * 100:.2f}%"
    except (ValueError, TypeError):
        return str(val).strip()


def pct_color(val):
    """Return (fg_color, bg_color, display_string) for a return value."""
    display = fmt_pct(val)
    if display == "—":
        return DARK_GRAY, WHITE, display
    try:
        f = float(val)
        if f > 0:
            return GREEN_FG, WHITE, display
        elif f < 0:
            return RED_FG, WHITE, display
        else:
            return DARK_GRAY, WHITE, display
    except (ValueError, TypeError):
        return DARK_GRAY, WHITE, display


def clean_acquirer(val):
    """Strip non-breaking spaces and tidy whitespace."""
    if val is None:
        return "—"
    return str(val).replace("\xa0", " ").strip()


# ── HTML builders ─────────────────────────────────────────────────────────────
# Padding tightened to 4px 4px so 15 columns fit within ~600px email width.

HEADER_STYLE = (
    f"font-size:8px;font-weight:bold;color:{BLUE_LITE};"
    f"padding:4px 4px;border-right:1px solid #1a6db5;"
)
HEADER_STYLE_LAST = (
    f"font-size:8px;font-weight:bold;color:{BLUE_LITE};"
    f"padding:4px 4px;"
)

COLUMNS = [
    ("Target",        "A"),
    ("Announced",     "B"),
    ("Acquirer",      "C"),
    ("Deal Type",     "D"),
    ("Closing Val",   "E"),
    ("Deal Price",    "F"),
    ("Last Price",    "G"),
    ("Pre-Deal",      "H"),
    ("Pre-Rumor",     "I"),
    ("Volume",        "J"),
    ("Options",       "K"),
    ("Div. Yield",    "L"),
    ("Est. Closing",  "M"),
    ("Return",        "N"),
    ("Ann. Return",   "O"),
]


def col_header_row():
    cells = ""
    for i, (label, _) in enumerate(COLUMNS):
        style = HEADER_STYLE if i < len(COLUMNS) - 1 else HEADER_STYLE_LAST
        cells += f'    <td style="{style}">{label}</td>\n'
    return f'  <tr style="background:{BLUE};">\n{cells}  </tr>\n'


def data_row(deal, bg):
    ticker    = deal["ticker"]
    announced = deal["announced"]
    acquirer  = deal["acquirer"]
    deal_type = deal["deal_type"]
    cl_value  = deal["closing_value"]
    deal_px   = deal["deal_price"]
    last_px   = deal["last_price"]
    pre_deal  = deal["pre_deal_price"]
    pre_rumor = deal["pre_rumor_price"]
    volume    = deal["volume"]
    options   = deal["options"]
    div_yield = deal["div_yield"]
    est_close = deal["est_closing"]
    ret       = deal["ret"]
    ann_ret   = deal["ann_ret"]

    border = f"border-bottom:1px solid {BLUE_LITE};"
    br     = f"border-right:1px solid {BLUE_LITE};"

    ret_fg, _, ret_disp     = pct_color(ret)
    ann_fg, _, ann_disp     = pct_color(ann_ret)
    opt_color = BLUE if str(options).strip().lower() == "yes" else MID_GRAY

    cells = (
        f'<td style="font-size:9px;font-weight:bold;color:{BLUE};padding:4px 4px;{border}{br}white-space:nowrap;">{ticker}</td>\n'
        f'<td style="font-size:8px;color:{DARK_GRAY};padding:4px 4px;{border}{br}white-space:nowrap;">{announced}</td>\n'
        f'<td style="font-size:8px;color:{DARK_GRAY};padding:4px 4px;{border}{br}">{acquirer}</td>\n'
        f'<td style="font-size:8px;color:{MID_GRAY};padding:4px 4px;{border}{br}font-style:italic;">{deal_type}</td>\n'
        f'<td style="font-size:8px;color:{DARK_GRAY};padding:4px 4px;{border}{br}text-align:center;white-space:nowrap;">{cl_value}</td>\n'
        f'<td style="font-size:8px;color:{DARK_GRAY};padding:4px 4px;{border}{br}text-align:center;white-space:nowrap;">{deal_px}</td>\n'
        f'<td style="font-size:8px;color:{DARK_GRAY};padding:4px 4px;{border}{br}text-align:center;white-space:nowrap;">{last_px}</td>\n'
        f'<td style="font-size:8px;color:{DARK_GRAY};padding:4px 4px;{border}{br}text-align:center;white-space:nowrap;">{pre_deal}</td>\n'
        f'<td style="font-size:8px;color:{DARK_GRAY};padding:4px 4px;{border}{br}text-align:center;white-space:nowrap;">{pre_rumor}</td>\n'
        f'<td style="font-size:8px;color:{DARK_GRAY};padding:4px 4px;{border}{br}text-align:center;white-space:nowrap;">{volume}</td>\n'
        f'<td style="font-size:8px;font-weight:bold;color:{opt_color};padding:4px 4px;{border}{br}text-align:center;">{options}</td>\n'
        f'<td style="font-size:8px;color:{DARK_GRAY};padding:4px 4px;{border}{br}text-align:center;white-space:nowrap;">{div_yield}</td>\n'
        f'<td style="font-size:8px;color:{DARK_GRAY};padding:4px 4px;{border}{br}text-align:center;white-space:nowrap;">{est_close}</td>\n'
        f'<td style="font-size:9px;font-weight:bold;color:{ret_fg};padding:4px 4px;{border}{br}text-align:center;white-space:nowrap;">{ret_disp}</td>\n'
        f'<td style="font-size:9px;font-weight:bold;color:{ann_fg};padding:4px 4px;{border}text-align:center;white-space:nowrap;">{ann_disp}</td>\n'
    )
    return f'  <tr style="background:{bg};">\n{cells}  </tr>\n'


# ── Excel reader ──────────────────────────────────────────────────────────────

def read_deals(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    deals = []

    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue  # skip header
        if not any(v is not None for v in row):
            continue  # skip empty rows

        # Detect whether col B is the "Track Deals" flag (string) or Announced Date
        col_b = row[1] if len(row) > 1 else None
        has_track_col = col_b is not None and not isinstance(col_b, (datetime, date)) and str(col_b).strip() != ""
        data = tuple(row[0:1]) + tuple(row[2:]) if has_track_col else tuple(row)
        # data order: ticker, ann, acq, dtype, cv, dp, lp, [pre_deal, pre_rumor,] vol, opt, dy, ec, ret, aret

        if len(data) >= 15:
            ticker, ann, acq, dtype, cv, dp, lp, pre_deal, pre_rumor, vol, opt, dy, ec, ret, aret = data[:15]
        elif len(data) >= 13:
            ticker, ann, acq, dtype, cv, dp, lp, vol, opt, dy, ec, ret, aret = data[:13]
            pre_deal = pre_rumor = None
        else:
            continue

        # Parse announced date for sorting
        if isinstance(ann, (datetime, date)):
            sort_key = ann if isinstance(ann, datetime) else datetime.combine(ann, datetime.min.time())
        else:
            try:
                sort_key = datetime.strptime(str(ann).strip(), "%m/%d/%y")
            except ValueError:
                sort_key = datetime.min

        deals.append({
            "sort_key":        sort_key,
            "ticker":          str(ticker).strip() if ticker else "—",
            "announced":       fmt_date(ann),
            "acquirer":        clean_acquirer(acq),
            "deal_type":       str(dtype).strip() if dtype else "—",
            "closing_value":   str(cv).strip() if cv else "—",
            "deal_price":      fmt_price(dp),
            "last_price":      fmt_price(lp),
            "pre_deal_price":  fmt_price(pre_deal),
            "pre_rumor_price": fmt_price(pre_rumor),
            "volume":          fmt_number(vol),
            "options":         str(opt).strip() if opt else "—",
            "div_yield":       fmt_yield(dy),
            "est_closing":     fmt_date(ec),
            "ret":             ret,
            "ann_ret":         aret,
        })

    # Sort by announced date, most recent first, take top N
    deals.sort(key=lambda d: d["sort_key"], reverse=True)
    return deals[:TOP_N]


# ── Main HTML assembly ────────────────────────────────────────────────────────

def generate_html(deals):
    rows_html = ""
    for i, deal in enumerate(deals):
        bg = STRIPE if i % 2 == 1 else WHITE
        rows_html += data_row(deal, bg)

    return f"""<table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-family:Arial,sans-serif;border-collapse:collapse;border:1px solid {BLUE_LITE};">

  <tr>
    <td colspan="15" style="background:{BLUE};padding:12px 16px;">
      <span style="font-size:15px;font-weight:bold;color:#ffffff;letter-spacing:0.3px;">Merger Arbitrage Tool</span>
      <span style="font-size:11px;color:#AACBE8;padding-left:12px;">Active Deal Tracker &nbsp;|&nbsp; WallachBeth Capital</span>
    </td>
  </tr>

{col_header_row()}
{rows_html}
  <tr>
    <td colspan="15" style="background:{BLUE};padding:6px 16px;text-align:center;">
      <span style="color:#99BFE3;font-size:10px;">WallachBeth Capital &nbsp;|&nbsp; Confidential &nbsp;|&nbsp; For Internal Use Only</span>
    </td>
  </tr>

</table>"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path  = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) >= 3 else "merger_arb.html"

    if not os.path.exists(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    print(f"Reading {input_path} ...")
    deals = read_deals(input_path)
    print(f"  -> {len(deals)} deals loaded (top {TOP_N} by announcement date)")

    html = generate_html(deals)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML written to {output_path}")


if __name__ == "__main__":
    main()
