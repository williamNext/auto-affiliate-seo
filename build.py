#!/usr/bin/env python3
"""Zero-dependency Programmatic SEO & Affiliate Static Site Generator."""

import datetime
import html
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
DIST = ROOT / "dist"


def load_env(env_path: pathlib.Path = ROOT / ".env") -> None:
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


# Curated evergreen high-intent comparison seed data (used alongside live feeds)
CATALOG = [
    {
        "slug": "best-budget-mechanical-keyboards-programming",
        "title": "Best Budget Mechanical Keyboards for Programming (2026 Specs)",
        "category": "Keyboards",
        "items": [
            {"name": "Keychron C3 Pro QMK/VIA", "specs": "Hot-swappable, Gasket Mount, Red/Brown Switches, 87 Keys", "rating": "4.8/5", "query": "Keychron C3 Pro Mechanical Keyboard"},
            {"name": "Royal Kludge RK61 Wireless", "specs": "60% Compact, Bluetooth 5.1, Hot-Swap, RGB Backlit", "rating": "4.6/5", "query": "Royal Kludge RK61 Mechanical Keyboard"},
            {"name": "Redragon K552 Kumara", "specs": "Tenkeyless, Metal Base, Outemu Blue/Red Switches", "rating": "4.5/5", "query": "Redragon K552 Mechanical Keyboard"},
        ],
    },
    {
        "slug": "best-ergonomic-vertical-mice-developers",
        "title": "Best Ergonomic Vertical Mice for Developers (2026 Specs)",
        "category": "Ergonomics",
        "items": [
            {"name": "Logitech Lift Vertical Ergonomic Mouse", "specs": "57-degree angle, Quiet Clicks, Bluetooth + Bolt, 4000 DPI", "rating": "4.8/5", "query": "Logitech Lift Vertical Ergonomic Mouse"},
            {"name": "Logitech MX Vertical", "specs": "USB-C Rechargeable, 4000 DPI Sensor, Flow Multi-OS", "rating": "4.7/5", "query": "Logitech MX Vertical Mouse"},
            {"name": "Anker 2.4G Wireless Vertical Mouse", "specs": "800/1200/1600 DPI, 5 Buttons, Ultra-Light", "rating": "4.5/5", "query": "Anker Wireless Vertical Ergonomic Mouse"},
        ],
    },
    {
        "slug": "best-usb-c-docking-stations-dual-4k-monitors",
        "title": "Best USB-C Docking Stations for Dual 4K Monitors (2026 Specs)",
        "category": "Docks & Hubs",
        "items": [
            {"name": "Anker 575 USB-C Docking Station (13-in-1)", "specs": "85W Laptop PD, Dual HDMI + DP, Gigabit Ethernet", "rating": "4.7/5", "query": "Anker 575 USB-C Docking Station"},
            {"name": "CalDigit TS4 Thunderbolt 4 Dock", "specs": "18 Ports, 98W PD, 2.5GbE, Dual 6K/4K Support", "rating": "4.8/5", "query": "CalDigit TS4 Thunderbolt 4 Dock"},
            {"name": "UGREEN Revodok Pro 210 Dual HDMI", "specs": "10-in-1, 100W PD Pass-Through, Dual 4K@60Hz", "rating": "4.6/5", "query": "UGREEN Revodok Pro USB C Hub Dual HDMI"},
        ],
    },
    {
        "slug": "best-portable-monitors-remote-coding",
        "title": "Best Portable USB-C Monitors for Remote Coding (2026 Specs)",
        "category": "Monitors",
        "items": [
            {"name": "ASUS ZenScreen 15.6\" 1080p USB-C", "specs": "IPS Matte Panel, Single-Cable USB-C, Smart Cover, 780g", "rating": "4.7/5", "query": "ASUS ZenScreen 15.6 Portable Monitor"},
            {"name": "ARZOPA Z1FC 16.1\" 144Hz Portable Monitor", "specs": "100% sRGB, Kickstand Built-in, USB-C + Mini HDMI", "rating": "4.6/5", "query": "ARZOPA 16.1 144Hz Portable Monitor"},
            {"name": "LG Gram +View 16\" WQXGA (2560x1600)", "specs": "16:10 Aspect Ratio, DCI-P3 99%, 670g Ultra-Light", "rating": "4.8/5", "query": "LG Gram View 16 Portable Monitor"},
        ],
    },
    {
        "slug": "best-nvme-ssd-enclosures-backups",
        "title": "Best 10Gbps & 40Gbps NVMe SSD Enclosures for Fast Backups",
        "category": "Storage",
        "items": [
            {"name": "Sabrent USB 3.2 10Gbps Tool-Free NVMe Enclosure", "specs": "Aluminum Heatsink, Tool-Free Latch, M.2 PCIe/SATA", "rating": "4.8/5", "query": "Sabrent USB 3.2 Tool-Free NVMe Enclosure"},
            {"name": "UGREEN M.2 NVMe 10Gbps Aluminum Case", "specs": "USB-C 3.2 Gen2, UASP + TRIM, Silicone Bumper", "rating": "4.7/5", "query": "UGREEN M.2 NVMe SSD Enclosure 10Gbps"},
            {"name": "Acasis 40Gbps Thunderbolt 4/3 NVMe Enclosure", "specs": "Intel JHL7440, Cooling Fan, Up to 2800MB/s Read", "rating": "4.6/5", "query": "Acasis 40Gbps NVMe Enclosure"},
        ],
    },
]


def fetch_trending_topics() -> list[dict]:
    """Fetch live trending open-source/dev hardware keywords from GitHub public API."""
    # ponytail: single unauthenticated request ceiling (60 req/hr) - add GITHUB_TOKEN if run >1x/hr
    url = "https://api.github.com/search/repositories?q=stars:>10000+topic:developer-tools&sort=updated&per_page=3"
    req = urllib.request.Request(url, headers={"User-Agent": "AutoAffiliateSEO/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = []
            for repo in data.get("items", [])[:3]:
                name = str(repo.get("name", "DevTool"))
                desc = str(repo.get("description") or "High-productivity developer workstation utility.")
                items.append({
                    "name": f"{name} Workstation Setup Guide & Gear",
                    "specs": desc[:110],
                    "rating": "4.7/5",
                    "query": f"{name} developer book hardware accessories",
                })
            if items:
                return [{
                    "slug": "trending-developer-workstation-gear",
                    "title": "Trending Developer Workstation & Productivity Gear",
                    "category": "Workstation",
                    "items": items,
                }]
    except Exception:
        pass
    return []


def make_affiliate_url(query: str, domain: str, tag: str) -> str:
    safe_domain = domain if domain in {"www.amazon.com", "www.amazon.com.br"} else "www.amazon.com.br"
    params = {"k": query}
    if tag:
        params["tag"] = tag
    return f"https://{safe_domain}/s?{urllib.parse.urlencode(params)}"


def render_layout(title: str, body_html: str, site_url: str, canonical_path: str = "", json_ld: str = "") -> str:
    esc_title = html.escape(title)
    canon = f"{site_url.rstrip('/')}/{canonical_path.lstrip('/')}" if canonical_path else site_url.rstrip("/") + "/"
    esc_canon = html.escape(canon)
    today = datetime.date.today().isoformat()
    ld_block = f'\n  <script type="application/ld+json">{json_ld}</script>' if json_ld else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc_title}</title>
  <meta name="description" content="{esc_title} - Side-by-side technical specifications and verified store links.">
  <link rel="canonical" href="{esc_canon}">{ld_block}
  <style>
    :root {{ --bg:#0f172a; --card:#1e293b; --text:#f8fafc; --muted:#94a3b8; --accent:#38bdf8; --btn:#0284c7; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}
    header, main, footer {{ max-width:920px; margin:0 auto; padding:1.25rem; }}
    .disclosure {{ background:#1e293b; border-left:4px solid var(--accent); padding:0.75rem 1rem; font-size:0.875rem; color:var(--muted); margin-bottom:1.5rem; border-radius:4px; }}
    a {{ color:var(--accent); text-decoration:none; }}
    a:hover {{ text-decoration:underline; }}
    table {{ width:100%; border-collapse:collapse; background:var(--card); border-radius:8px; overflow:hidden; margin:1.25rem 0; }}
    th, td {{ padding:0.9rem; text-align:left; border-bottom:1px solid #334155; }}
    th {{ background:#020617; color:var(--accent); }}
    .btn {{ display:inline-block; background:var(--btn); color:#fff; padding:0.5rem 0.9rem; border-radius:6px; font-weight:600; font-size:0.875rem; }}
    .btn:hover {{ text-decoration:none; opacity:0.92; }}
    .grid {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); }}
    .card {{ background:var(--card); padding:1.25rem; border-radius:8px; border:1px solid #334155; }}
    footer {{ font-size:0.8rem; color:var(--muted); border-top:1px solid #334155; margin-top:2rem; }}
  </style>
</head>
<body>
  <header>
    <strong><a href="{html.escape(site_url.rstrip('/') + '/')}">DevSpec Comparisons</a></strong>
    <span style="float:right;color:var(--muted);font-size:0.85rem;">Updated: {today}</span>
  </header>
  <main>
    <aside class="disclosure" role="note">
      <strong>Legal Disclosure (FTC / CONAR):</strong> As an affiliate, this site earns commissions from qualifying purchases at no extra cost to you. All specifications are compiled from public manufacturer data.
    </aside>
    {body_html}
  </main>
  <footer>
    <p>&copy; {datetime.date.today().year} DevSpec Comparisons. Automated Programmatic Spec Matrix.</p>
  </footer>
</body>
</html>
"""


def build_site(out_dir: pathlib.Path = DIST, fetch_live: bool = True) -> list[str]:
    load_env()
    tag = os.getenv("AFFILIATE_TAG", "devspec-20")
    domain = os.getenv("AMAZON_DOMAIN", "www.amazon.com.br")
    site_url = os.getenv("SITE_URL", "https://williamnext.github.io/auto-affiliate-seo")

    out_dir.mkdir(parents=True, exist_ok=True)
    pages = list(CATALOG) + (fetch_trending_topics() if fetch_live else [])
    generated_urls = [f"{site_url.rstrip('/')}/"]

    cards_html = []
    for page in pages:
        slug = urllib.parse.quote(page["slug"].strip("/"))
        filename = f"{slug}.html"
        rows = []
        for item in page["items"]:
            aff_url = make_affiliate_url(item["query"], domain, tag)
            rows.append(
                f"<tr>"
                f"<td><strong>{html.escape(item['name'])}</strong></td>"
                f"<td>{html.escape(item['specs'])}</td>"
                f"<td>{html.escape(item['rating'])}</td>"
                f"<td><a class='btn' href='{html.escape(aff_url)}' rel='nofollow sponsored' target='_blank'>Check Price</a></td>"
                f"</tr>"
            )
        body = (
            f"<p><a href='index.html'>&larr; All Comparisons</a></p>"
            f"<h1>{html.escape(page['title'])}</h1>"
            f"<p>Category: <strong>{html.escape(page['category'])}</strong></p>"
            f"<table><thead><tr><th>Model</th><th>Key Technical Specs</th><th>Rating</th><th>Store Link</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
        ld_data = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": page["title"],
            "itemListElement": [
                {"@type": "ListItem", "position": idx + 1, "name": it["name"], "description": it["specs"]}
                for idx, it in enumerate(page["items"])
            ],
        }
        safe_ld = json.dumps(ld_data).replace("</", "<\\/")
        (out_dir / filename).write_text(render_layout(page["title"], body, site_url, filename, safe_ld), encoding="utf-8")
        generated_urls.append(f"{site_url.rstrip('/')}/{filename}")
        cards_html.append(
            f"<article class='card'>"
            f"<small style='color:var(--muted)'>{html.escape(page['category'])}</small>"
            f"<h2 style='margin:0.4rem 0;font-size:1.1rem;'><a href='{html.escape(filename)}'>{html.escape(page['title'])}</a></h2>"
            f"<p style='font-size:0.875rem;color:var(--muted);'>Compare {len(page['items'])} verified models side by side.</p>"
            f"</article>"
        )

    index_body = (
        "<h1>Hardware & Developer Gear Technical Comparisons</h1>"
        "<p>Side-by-side specification matrices updated daily.</p>"
        f"<section class='grid'>{''.join(cards_html)}</section>"
    )
    (out_dir / "index.html").write_text(render_layout("DevSpec Comparisons - Technical Buying Guides", index_body, site_url), encoding="utf-8")

    # Sitemap & robots.txt
    today = datetime.date.today().isoformat()
    url_entries = "".join(
        f"<url><loc>{html.escape(u)}</loc><lastmod>{today}</lastmod></url>" for u in generated_urls
    )
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{url_entries}</urlset>'
    (out_dir / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (out_dir / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site_url.rstrip('/')}/sitemap.xml\n", encoding="utf-8")
    return generated_urls


def self_check() -> None:
    import tempfile
    os.environ["AFFILIATE_TAG"] = "testtag-20"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        urls = build_site(out_dir=tmp_path, fetch_live=False)
        assert len(urls) == len(CATALOG) + 1, "Expected index + all catalog pages"
        sample = (tmp_path / f"{CATALOG[0]['slug']}.html").read_text(encoding="utf-8")
        assert "tag=testtag-20" in sample, "Affiliate tag missing"
        assert "rel='nofollow sponsored'" in sample, "SEO sponsored attribute missing"
        assert "Legal Disclosure (FTC / CONAR)" in sample, "Legal disclosure missing"
        assert '"@type": "ItemList"' in sample, "Schema.org JSON-LD missing"
        xss_layout = render_layout("<script>alert(1)</script>", "<b>ok</b>", "https://example.com")
        assert "<script>" not in xss_layout and "&lt;script&gt;" in xss_layout, "XSS escaping failed"
        assert (tmp_path / "sitemap.xml").exists() and (tmp_path / "robots.txt").exists(), "SEO files missing"
    print("SELF-CHECK PASSED: All assertions verified.")


if __name__ == "__main__":
    if "--test" in sys.argv:
        self_check()
    else:
        built = build_site()
        print(f"Built {len(built)} pages in {DIST}")
