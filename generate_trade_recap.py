#!/usr/bin/env python3
"""
WallachBeth Trade Recap HTML Generator
---------------------------------------
Parses a plain-text trade recap file and outputs a branded HTML table.
 
Usage:
    python generate_trade_recap.py <input.txt> [output.html]
 
Arguments:
    input.txt     Path to the trade recap text file
    output.html   Optional output path (default: trade_recap.html)
 
Expected input format:
    Trade Recap: <date>
    ----------
    Color - <trade description text>
    <TICKER> <leg> OI Change: <+/-value>
    <TICKER> <leg> OI Change: <+/-value>   (optional second leg)
    —-------
    ... repeat for each trade block
"""
 
import sys, re, os
 
BLUE      = "#08519C"
BLUE_LITE = "#DEEBF7"
STRIPE    = "#F2F7FC"
WHITE     = "#ffffff"
DARK_GRAY = "#3D3D3D"
GREEN_BG  = "#e6f4ec"
GREEN_FG  = "#1A7C3E"
RED_BG    = "#fdeaea"
RED_FG    = "#C0392B"
 
 
def is_separator(line):
    s = line.strip().replace("\u2014","-").replace("\u2013","-").replace("\u2012","-")
    return bool(re.match(r'^-{3,}$', s))
 
 
def parse_date(line):
    m = re.search(r'Trade Recap[:\s]+(.+)', line, re.IGNORECASE)
    return m.group(1).strip() if m else ""
 
 
def parse_oi_line(line):
    """'WBD Oct 20 Put OI Change: +1,309' -> ('WBD Oct 20 Put OI Change', '+1,309')"""
    m = re.match(r'^(.+?)\s+OI\s+Change\s*:\s*([+-]?\s*[\d,]+)', line.strip(), re.IGNORECASE)
    if not m:
        return None, None
    label = m.group(1).strip() + " OI Change"
    raw = m.group(2).replace(',','').replace(' ','')
    try:
        n = int(raw)
        val = f"+{n:,}" if n >= 0 else f"{n:,}"
    except ValueError:
        val = m.group(2).strip()
    return label, val
 
 
def is_live(text):
    return bool(re.search(r'\blive\b', text, re.IGNORECASE))
 
 
def parse_file(path):
    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip('\n') for l in f]
 
    date_str      = ""
    trades        = []
    current_trade = None
    current_oi    = []
 
    def flush():
        nonlocal current_trade, current_oi
        if current_trade:
            current_trade["oi"] = current_oi
            trades.append(current_trade)
        current_trade = None
        current_oi    = []
 
    for line in lines:
        s = line.strip()
        if not s: continue
        if re.match(r'trade recap', s, re.IGNORECASE):
            date_str = parse_date(s); continue
        if is_separator(s):
            flush(); continue
        oi_label, oi_value = parse_oi_line(s)
        if oi_label:
            current_oi.append((oi_label, oi_value)); continue
        if re.match(r'color\s*-', s, re.IGNORECASE):
            flush()
            # Strip the "Color - " prefix, keep everything else verbatim
            desc = re.sub(r'^color\s*-\s*', '', s, flags=re.IGNORECASE).strip()
            current_trade = {"desc": desc, "live": is_live(desc)}
            current_oi = []
            continue
 
    flush()
    return date_str, trades
 
 
def oi_badge(val):
    try:
        n = int(val.replace(',','').replace('+',''))
        bg,fg = (GREEN_BG,GREEN_FG) if n>0 else (RED_BG,RED_FG) if n<0 else (BLUE_LITE,BLUE)
    except ValueError:
        bg,fg = BLUE_LITE,BLUE
    return (f'<span style="background:{bg};color:{fg};font-size:12px;'
            f'font-weight:bold;padding:2px 10px;">{val}</span>')
 
 
def build_html(date_str, trades):
    rows = []
    for i, t in enumerate(trades):
        desc = t.get("desc", "")
        live = t.get("live", False)
        oi   = t.get("oi", [])
 
        pill = (f'<span style="background:{BLUE_LITE};color:{BLUE};font-size:10px;'
                f'font-weight:bold;padding:2px 8px;">LIVE</span>') if live else ""
        top = "border-top:1px solid #1a6db5;" if i == 0 else ""
 
        rows.append(
            f'  <tr><td colspan="2" style="background:{BLUE};padding:10px 16px;{top}border-bottom:1px solid #1a6db5;">\n'
            f'    <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>\n'
            f'      <td style="font-size:12px;color:#ffffff;">{desc}</td>\n'
            f'      <td align="right" style="white-space:nowrap;padding-left:12px;">{pill}</td>\n'
            f'    </tr></table>\n  </td></tr>'
        )
        for j, (lbl, val) in enumerate(oi):
            bg = STRIPE if j % 2 == 1 else WHITE
            rows.append(
                f'  <tr>\n'
                f'    <td style="font-size:11px;color:{DARK_GRAY};padding:7px 16px;'
                f'border-bottom:1px solid {BLUE_LITE};background:{bg};">{lbl}</td>\n'
                f'    <td align="right" style="padding:7px 16px;border-bottom:1px solid {BLUE_LITE};'
                f'background:{bg};">{oi_badge(val)}</td>\n'
                f'  </tr>'
            )
 
    body = "\n".join(rows)
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="font-family:Arial,sans-serif;border-collapse:collapse;border:1px solid {BLUE_LITE};">\n\n'
        f'  <tr><td colspan="2" style="background:{BLUE};padding:12px 16px;text-align:left;">\n'
        f'    <span style="font-size:15px;font-weight:bold;color:#ffffff;letter-spacing:0.3px;">'
        f'Trade Recap ({date_str})</span>\n'
        f'  </td></tr>\n\n'
        f'{body}\n\n'
        f'  <tr><td colspan="2" style="background:{BLUE};padding:6px 16px;text-align:center;">\n'
        f'    <span style="color:#99BFE3;font-size:10px;">WallachBeth Capital'
        f' &nbsp;|&nbsp; Confidential &nbsp;|&nbsp; For Internal Use Only</span>\n'
        f'  </td></tr>\n\n</table>'
    )
 
 
def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) >= 3 else "trade_recap.html"
    if not os.path.exists(inp):
        print(f"Error: file not found: {inp}"); sys.exit(1)
    print(f"Parsing {inp} ...")
    date_str, trades = parse_file(inp)
    print(f"  -> date:   {date_str}")
    print(f"  -> trades: {len(trades)}")
    for t in trades:
        print(f"     live={t['live']}  oi={len(t['oi'])}  {t['desc'][:60]}")
    html = build_html(date_str, trades)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML written to {out}")
 
if __name__ == "__main__":
    main()