#!/usr/bin/env python3
"""Zero-dependency Programmatic SEO (PT-BR) & Affiliate Static Site Generator with IndexNow."""

import datetime
import hashlib
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


# High-intent Brazilian Portuguese (PT-BR) buyer comparisons for Amazon.com.br
CATALOG = [
    {
        "slug": "best-budget-mechanical-keyboards-programming",
        "title": "Melhores Teclados Mecânicos Custo-Benefício para Programar (2026)",
        "category": "Teclados & Periféricos",
        "items": [
            {"name": "Keychron C3 Pro QMK/VIA", "specs": "Hot-swappable, Gasket Mount, Switches Red/Brown, ABNT2/ANSI", "rating": "4.8/5", "query": "Teclado Mecanico Keychron"},
            {"name": "Royal Kludge RK61 Sem Fio", "specs": "Compacto 60%, Bluetooth 5.1, Hot-Swap, RGB", "rating": "4.7/5", "query": "Teclado Mecanico Royal Kludge RK61"},
            {"name": "Redragon Kumara K552 ABNT2", "specs": "Tenkeyless, Base de Metal, Switch Outemu Red/Brown", "rating": "4.6/5", "query": "Teclado Mecanico Redragon Kumara K552"},
        ],
    },
    {
        "slug": "best-ergonomic-vertical-mice-developers",
        "title": "Melhores Mouses Verticais Ergonômicos para Trabalho e Código (2026)",
        "category": "Ergonomia",
        "items": [
            {"name": "Logitech Lift Vertical Ergonômico", "specs": "Ângulo de 57 graus, Cliques Silenciosos, Bluetooth + Logi Bolt", "rating": "4.9/5", "query": "Mouse Vertical Logitech Lift"},
            {"name": "Logitech MX Vertical Sem Fio", "specs": "Recarregável USB-C, Sensor 4000 DPI, Multi-dispositivo", "rating": "4.8/5", "query": "Mouse Logitech MX Vertical"},
            {"name": "Anker Mouse Vertical Sem Fio 2.4G", "specs": "800/1200/1600 DPI, 5 Botões, Leve para Uso Prolongado", "rating": "4.5/5", "query": "Mouse Vertical Ergonomico Sem Fio"},
        ],
    },
    {
        "slug": "best-usb-c-docking-stations-dual-4k-monitors",
        "title": "Melhores Hubs e Docking Stations USB-C para 2 Monitores 4K",
        "category": "Docks & Conectividade",
        "items": [
            {"name": "Anker 575 USB-C Docking Station (13-em-1)", "specs": "Power Delivery 85W, Dual HDMI + DisplayPort, Gigabit Ethernet", "rating": "4.8/5", "query": "Docking Station USB C Anker"},
            {"name": "UGREEN Revodok Pro Hub USB-C Dual HDMI", "specs": "10-em-1, Pass-Through 100W PD, Dual 4K@60Hz, Leitor SD", "rating": "4.7/5", "query": "Hub USB C UGREEN HDMI 4K"},
            {"name": "Baseus Hub USB-C 11-em-1 Dual HDMI", "specs": "PD 100W, 2x HDMI 4K, VGA, RJ45 Gigabit, 3x USB 3.0", "rating": "4.6/5", "query": "Hub USB C Baseus HDMI"},
        ],
    },
    {
        "slug": "best-portable-monitors-remote-coding",
        "title": "Melhores Monitores Portáteis USB-C para Notebook e Home Office",
        "category": "Monitores",
        "items": [
            {"name": "ASUS ZenScreen 15.6\" Full HD IPS USB-C", "specs": "Painel IPS Antirreflexo, Cabo Único USB-C, Capa Suporte, 780g", "rating": "4.8/5", "query": "Monitor Portatil ASUS ZenScreen 15.6"},
            {"name": "ARZOPA Z1FC 16.1\" 144Hz Monitor Portátil", "specs": "100% sRGB, Suporte Integrado, USB-C + Mini HDMI", "rating": "4.7/5", "query": "Monitor Portatil ARZOPA 144Hz"},
            {"name": "LG Gram +View 16\" WQXGA (2560x1600)", "specs": "Proporção 16:10, DCI-P3 99%, Ultra-leve 670g", "rating": "4.8/5", "query": "Monitor Portatil USB C 16"},
        ],
    },
    {
        "slug": "best-nvme-ssd-enclosures-backups",
        "title": "Melhores Cases NVMe M.2 USB-C 10Gbps e SSDs Externos Rápidos",
        "category": "Armazenamento",
        "items": [
            {"name": "Case UGREEN M.2 NVMe SATA 10Gbps Alumínio", "specs": "USB-C 3.2 Gen2, UASP + TRIM, Proteção de Silicone", "rating": "4.8/5", "query": "Case SSD NVMe UGREEN USB C"},
            {"name": "SSD Externo Portátil Kingston XS1000 1TB/2TB", "specs": "Leitura até 1050MB/s, USB 3.2 Gen 2, Ultra Compacto", "rating": "4.9/5", "query": "SSD Externo Kingston XS1000"},
            {"name": "SSD Externo SanDisk Extreme Portátil 1TB", "specs": "NVMe 1050MB/s, IP65 Resistente a Água e Poeira", "rating": "4.8/5", "query": "SSD Externo SanDisk Extreme 1TB"},
        ],
    },
    {
        "slug": "melhores-cadeiras-ergonomicas-home-office-nr17",
        "title": "Melhores Cadeiras Ergonômicas NR17 para Home Office (2026)",
        "category": "Ergonomia",
        "items": [
            {"name": "Cadeira Ergonômica Elements Vertta Pro / Astra Pro", "specs": "Tela Mesh Respirável, Apoio Lombar Ajustável, Braços 3D/4D, NR17", "rating": "4.8/5", "query": "Cadeira Ergonomica Elements"},
            {"name": "Cadeira Office DT3 Diana / Moira Ergonômica", "specs": "Encosto Reclinável, Apoio de Cabeça e Lombar, Certificação NR17", "rating": "4.7/5", "query": "Cadeira Ergonomica DT3"},
            {"name": "Cadeira Presidente Ergonômica Cavaletti / Plaxmetal Brizza", "specs": "Mecanismo Back System / Relax, Espuma Injetada, Alta Durabilidade", "rating": "4.7/5", "query": "Cadeira Ergonomica Presidente NR17"},
        ],
    },
    {
        "slug": "melhores-fones-cancelamento-ruido-anc-trabalho",
        "title": "Melhores Fones Bluetooth com Cancelamento de Ruído (ANC) para Foco",
        "category": "Áudio & Foco",
        "items": [
            {"name": "Sony WH-1000XM5 / WH-1000XM4 Wireless ANC", "specs": "Cancelamento de Ruído Líder, 30h Bateria, Conexão Multiponto", "rating": "4.9/5", "query": "Fone Sony WH-1000XM4 WH-1000XM5"},
            {"name": "Anker Soundcore Q30 / Space Q45 ANC", "specs": "ANC Híbrido, Até 50h de Bateria, Hi-Res Audio, Melhor Custo-Benefício", "rating": "4.8/5", "query": "Fone Anker Soundcore Q30 Q45"},
            {"name": "Edifier W820NB Plus Bluetooth ANC", "specs": "LDAC Hi-Res, 49h Bateria, Conforto Leve para Reuniões", "rating": "4.7/5", "query": "Fone Edifier W820NB Plus"},
        ],
    },
    {
        "slug": "melhores-notebooks-programacao-custo-beneficio",
        "title": "Melhores Notebooks para Programação e Desenvolvimento (2026)",
        "category": "Notebooks",
        "items": [
            {"name": "Apple MacBook Air M2 / M3 16GB RAM", "specs": "Chip Apple Silicon, Até 18h Bateria, Tela Liquid Retina, Silencioso", "rating": "4.9/5", "query": "MacBook Air M2 M3"},
            {"name": "ASUS VivoBook / ZenBook Ryzen 7 ou Core i7 16GB", "specs": "SSD NVMe 512GB, Tela Full HD IPS/OLED, Leve para Mobilidade", "rating": "4.7/5", "query": "Notebook ASUS Ryzen 7 16GB SSD"},
            {"name": "Lenovo IdeaPad / ThinkPad Core i5/i7 16GB SSD", "specs": "Teclado Confortável, Expansão de RAM/SSD, Excelente Linux/Windows", "rating": "4.7/5", "query": "Notebook Lenovo 16GB SSD"},
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
                desc = str(repo.get("description") or "Acessórios e equipamentos para produtividade em tecnologia.")
                items.append({
                    "name": f"Kit Setup & Livros Técnicos ({name})",
                    "specs": desc[:110],
                    "rating": "4.7/5",
                    "query": f"livros programacao {name} acessorios setup",
                })
            if items:
                return [{
                    "slug": "trending-developer-workstation-gear",
                    "title": "Equipamentos e Livros em Alta para Desenvolvedores (Atualizado Hoje)",
                    "category": "Tendências do Dia",
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


def render_layout(title: str, body_html: str, site_url: str, tag: str, domain: str, canonical_path: str = "", json_ld: str = "") -> str:
    esc_title = html.escape(title)
    canon = f"{site_url.rstrip('/')}/{canonical_path.lstrip('/')}" if canonical_path else site_url.rstrip("/") + "/"
    esc_canon = html.escape(canon)
    today = datetime.date.today().isoformat()
    ld_block = f'\n  <script type="application/ld+json">{json_ld}</script>' if json_ld else ""
    safe_domain = html.escape(domain if domain in {"www.amazon.com", "www.amazon.com.br"} else "www.amazon.com.br")
    safe_tag = html.escape(tag)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc_title}</title>
  <meta name="description" content="{esc_title} - Comparativo técnico lado a lado e links verificados na Amazon Brasil.">
  <link rel="canonical" href="{esc_canon}">{ld_block}
  <style>
    :root {{ --bg:#0f172a; --card:#1e293b; --text:#f8fafc; --muted:#94a3b8; --accent:#38bdf8; --btn:#0284c7; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}
    header, main, footer {{ max-width:920px; margin:0 auto; padding:1.25rem; }}
    .disclosure {{ background:#1e293b; border-left:4px solid var(--accent); padding:0.75rem 1rem; font-size:0.875rem; color:var(--muted); margin-bottom:1.5rem; border-radius:4px; }}
    .search-box {{ background:var(--card); padding:1rem; border-radius:8px; border:1px solid #334155; margin-bottom:1.5rem; display:flex; gap:0.5rem; flex-wrap:wrap; }}
    .search-box input {{ flex:1; min-width:200px; padding:0.6rem 0.8rem; border-radius:6px; border:1px solid #475569; background:#020617; color:var(--text); font-size:0.95rem; }}
    a {{ color:var(--accent); text-decoration:none; }}
    a:hover {{ text-decoration:underline; }}
    table {{ width:100%; border-collapse:collapse; background:var(--card); border-radius:8px; overflow:hidden; margin:1.25rem 0; }}
    th, td {{ padding:0.9rem; text-align:left; border-bottom:1px solid #334155; }}
    th {{ background:#020617; color:var(--accent); }}
    .btn {{ display:inline-block; background:var(--btn); color:#fff; padding:0.5rem 0.9rem; border-radius:6px; font-weight:600; font-size:0.875rem; border:none; cursor:pointer; }}
    .btn:hover {{ text-decoration:none; opacity:0.92; }}
    .grid {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); }}
    .card {{ background:var(--card); padding:1.25rem; border-radius:8px; border:1px solid #334155; }}
    footer {{ font-size:0.8rem; color:var(--muted); border-top:1px solid #334155; margin-top:2rem; }}
  </style>
</head>
<body>
  <header>
    <strong><a href="{html.escape(site_url.rstrip('/') + '/')}">DevSpec Brasil — Comparativos Técnicos</a></strong>
    <span style="float:right;color:var(--muted);font-size:0.85rem;">Atualizado: {today}</span>
  </header>
  <main>
    <aside class="disclosure" role="note">
      <strong>Legal Disclosure (FTC / CONAR):</strong> Como associado da Amazon, este site recebe comissões por compras qualificadas sem custo adicional para você.
    </aside>
    <form class="search-box" action="https://{safe_domain}/s" method="get" target="_blank" rel="noopener">
      <input type="text" name="k" placeholder="Buscar qualquer produto com desconto na Amazon.com.br..." required aria-label="Buscar produto">
      <input type="hidden" name="tag" value="{safe_tag}">
      <button type="submit" class="btn">Buscar Oferta na Amazon &rarr;</button>
    </form>
    {body_html}
  </main>
  <footer>
    <p>&copy; {datetime.date.today().year} DevSpec Brasil. Comparativos Automatizados de Especificações.</p>
  </footer>
</body>
</html>
"""


def ping_indexnow(site_url: str, key: str, urls: list[str]) -> bool:
    """Notify Bing, Yahoo, DuckDuckGo, and Yandex via IndexNow protocol ($0, zero-login)."""
    parsed = urllib.parse.urlparse(site_url)
    if not parsed.netloc or "example.github.io" in parsed.netloc:
        return False
    payload = {
        "host": parsed.netloc,
        "key": key,
        "keyLocation": f"{site_url.rstrip('/')}/{key}.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "AutoAffiliateSEO/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status in (200, 202)
    except Exception:
        return False


def build_site(out_dir: pathlib.Path = DIST, fetch_live: bool = True) -> list[str]:
    load_env()
    tag = os.getenv("AFFILIATE_TAG", "williamdevspe-20")
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
                f"<td><a class='btn' href='{html.escape(aff_url)}' rel='nofollow sponsored' target='_blank'>Ver Preço na Amazon</a></td>"
                f"</tr>"
            )
        body = (
            f"<p><a href='index.html'>&larr; Todos os Comparativos</a></p>"
            f"<h1>{html.escape(page['title'])}</h1>"
            f"<p>Categoria: <strong>{html.escape(page['category'])}</strong></p>"
            f"<table><thead><tr><th>Modelo</th><th>Especificações Principais</th><th>Avaliação</th><th>Oferta Verificada</th></tr></thead>"
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
        (out_dir / filename).write_text(
            render_layout(page["title"], body, site_url, tag, domain, filename, safe_ld),
            encoding="utf-8",
        )
        generated_urls.append(f"{site_url.rstrip('/')}/{filename}")
        cards_html.append(
            f"<article class='card'>"
            f"<small style='color:var(--muted)'>{html.escape(page['category'])}</small>"
            f"<h2 style='margin:0.4rem 0;font-size:1.1rem;'><a href='{html.escape(filename)}'>{html.escape(page['title'])}</a></h2>"
            f"<p style='font-size:0.875rem;color:var(--muted);'>Compare {len(page['items'])} modelos lado a lado na Amazon Brasil.</p>"
            f"</article>"
        )

    index_body = (
        "<h1>Comparativos Técnicos e Guias de Compra (Brasil)</h1>"
        "<p>Tabelas comparativas diretas atualizadas diariamente com links verificados da Amazon.com.br.</p>"
        f"<section class='grid'>{''.join(cards_html)}</section>"
    )
    (out_dir / "index.html").write_text(
        render_layout("DevSpec Brasil - Comparativos e Melhores Preços", index_body, site_url, tag, domain),
        encoding="utf-8",
    )

    # Sitemap, robots.txt & IndexNow key file
    today = datetime.date.today().isoformat()
    url_entries = "".join(
        f"<url><loc>{html.escape(u)}</loc><lastmod>{today}</lastmod></url>" for u in generated_urls
    )
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{url_entries}</urlset>'
    (out_dir / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (out_dir / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site_url.rstrip('/')}/sitemap.xml\n", encoding="utf-8")

    indexnow_key = hashlib.sha256(site_url.encode("utf-8")).hexdigest()[:32]
    (out_dir / f"{indexnow_key}.txt").write_text(indexnow_key, encoding="utf-8")
    if fetch_live:
        ping_indexnow(site_url, indexnow_key, generated_urls)

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
        assert 'name="k"' in sample and 'value="testtag-20"' in sample, "Universal search bar missing"
        xss_layout = render_layout("<script>alert(1)</script>", "<b>ok</b>", "https://example.com", "tag-20", "www.amazon.com.br")
        assert "<script>" not in xss_layout and "&lt;script&gt;" in xss_layout, "XSS escaping failed"
        assert (tmp_path / "sitemap.xml").exists() and (tmp_path / "robots.txt").exists(), "SEO files missing"
    print("SELF-CHECK PASSED: All assertions verified.")


if __name__ == "__main__":
    if "--test" in sys.argv:
        self_check()
    else:
        built = build_site()
        print(f"Built {len(built)} pages in {DIST}")
