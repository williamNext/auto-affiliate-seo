#!/usr/bin/env python3
"""Zero-dependency Social Media Deal Publisher & Comment Keyword Auto-Responder (X, Instagram, Facebook)."""

import base64
import datetime
import hashlib
import hmac
import json
import os
import pathlib
import random
import re
import secrets
import sys
import time
import urllib.parse
import urllib.request

from build import CATALOG, load_env, make_affiliate_url

ROOT = pathlib.Path(__file__).resolve().parent

# Brazilian Portuguese conversational stopwords stripped when isolating product keywords from comments
PT_STOPWORDS = {
    "oi", "ola", "olá", "opa", "bom", "boa", "dia", "tarde", "noite", "eu", "quero", "queria",
    "gostaria", "comprar", "procuro", "procurando", "preciso", "busco", "buscando", "de", "do",
    "da", "dos", "das", "um", "uma", "uns", "umas", "algum", "alguma", "me", "indica", "indique",
    "recomenda", "recomende", "manda", "envia", "qual", "quais", "o", "a", "os", "as", "melhor",
    "melhores", "tem", "teria", "promocao", "promoção", "oferta", "desconto", "cupom", "link",
    "para", "pra", "por", "favor", "pfv", "barato", "barata", "em", "conta", "custo", "beneficio",
    "benefício", "voce", "você", "vcs", "acha", "encontra", "ver", "preco", "preço", "valor",
    "estou", "to", "tô", "cade", "cadê", "onde", "como", "ai", "aí", "aqui", "hoje", "agora",
}


def extract_product_keyword(comment_text: str) -> str:
    """Extract clean product search query from any free-form Portuguese comment."""
    cleaned = re.sub(r"https?://\S+", " ", comment_text.lower())
    cleaned = re.sub(r"[^\w\s\-]", " ", cleaned, flags=re.UNICODE)
    tokens = [t for t in cleaned.split() if len(t) > 1 and t not in PT_STOPWORDS]
    return " ".join(tokens[:6]).strip()


def build_reply_message(comment_text: str, tag: str = "williamdevspe-20", domain: str = "www.amazon.com.br") -> tuple[str, str]:
    """Return (extracted_keyword, formatted_reply_with_affiliate_link)."""
    keyword = extract_product_keyword(comment_text)
    if not keyword:
        return "", ""
    url = make_affiliate_url(keyword, domain, tag)
    reply = (
        f"Encontrei! Confira as melhores ofertas verificadas de '{keyword}' na Amazon: "
        f"{url} #publi [Afiliado]"
    )
    return keyword, reply


def build_daily_deal_post(tag: str = "williamdevspe-20", domain: str = "www.amazon.com.br", site_url: str = "https://williamnext.github.io/auto-affiliate-seo") -> dict[str, str]:
    """Pick a high-converting deal + engagement CTA for daily social posting."""
    all_items = [
        (page["category"], item)
        for page in CATALOG
        for item in page["items"]
    ]
    day_seed = int(datetime.date.today().strftime("%Y%m%d")) + datetime.datetime.now(datetime.timezone.utc).hour
    rng = random.Random(day_seed)
    category, item = rng.choice(all_items)
    aff_url = make_affiliate_url(item["query"], domain, tag)

    post_text = (
        f"🔥 Destaque em {category}: {item['name']}\n"
        f"✅ {item['specs']} (Avaliação {item['rating']})\n"
        f"🛒 Ver preço na Amazon: {aff_url}\n\n"
        f"💬 Procurando outro produto? Comente o nome de QUALQUER item aqui embaixo "
        f"que nosso robô responde na hora com o link da oferta! #publi #ofertas"
    )
    return {
        "name": item["name"],
        "text": post_text,
        "url": aff_url,
        "site_url": site_url,
    }


def _http_json(url: str, method: str = "GET", data: dict | None = None, form: dict | None = None, headers: dict | None = None) -> dict:
    hdrs = {"User-Agent": "AutoAffiliateBot/1.0"}
    if headers:
        hdrs.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    elif form is not None:
        body = urllib.parse.urlencode(form).encode("utf-8")
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --- 1. X (Twitter) API v2 (OAuth 1.0a Pure Stdlib) ---

def _oauth1_header(method: str, url: str, ck: str, cs: str, at: str, ats: str, nonce: str = "", ts: str = "") -> str:
    oauth_params = {
        "oauth_consumer_key": ck,
        "oauth_nonce": nonce or secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": ts or str(int(time.time())),
        "oauth_token": at,
        "oauth_version": "1.0",
    }
    param_str = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
        for k, v in sorted(oauth_params.items())
    )
    base_str = "&".join([
        method.upper(),
        urllib.parse.quote(url, safe=""),
        urllib.parse.quote(param_str, safe=""),
    ])
    signing_key = f"{urllib.parse.quote(cs, safe='')}&{urllib.parse.quote(ats, safe='')}"
    sig = base64.b64encode(hmac.new(signing_key.encode("utf-8"), base_str.encode("utf-8"), hashlib.sha1).digest()).decode("utf-8")
    oauth_params["oauth_signature"] = sig
    header_parts = ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )
    return f"OAuth {header_parts}"


def post_x_tweet(text: str, reply_to_id: str = "") -> dict | None:
    ck = os.getenv("X_API_KEY", "")
    cs = os.getenv("X_API_SECRET", "")
    at = os.getenv("X_ACCESS_TOKEN", "")
    ats = os.getenv("X_ACCESS_SECRET", "")
    if not (ck and cs and at and ats):
        return None
    url = "https://api.twitter.com/2/tweets"
    payload: dict = {"text": text[:280]}
    if reply_to_id:
        payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}
    auth = _oauth1_header("POST", url, ck, cs, at, ats)
    return _http_json(url, method="POST", data=payload, headers={"Authorization": auth})


# --- 2. Facebook Page Graph API ---

def post_facebook_page(message: str, link: str) -> dict | None:
    page_id = os.getenv("FB_PAGE_ID", "")
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    if not (page_id and token):
        return None
    url = f"https://graph.facebook.com/v21.0/{urllib.parse.quote(page_id)}/feed"
    return _http_json(url, method="POST", form={"message": message, "link": link, "access_token": token})


def reply_facebook_comments(tag: str, domain: str) -> int:
    page_id = os.getenv("FB_PAGE_ID", "")
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    if not (page_id and token):
        return 0
    replied = 0
    posts_url = f"https://graph.facebook.com/v21.0/{urllib.parse.quote(page_id)}/posts?fields=id,comments{{id,message,from,comments{{message}}}}&limit=5&access_token={urllib.parse.quote(token)}"
    data = _http_json(posts_url)
    for post in data.get("data", []):
        for comment in post.get("comments", {}).get("data", []):
            cid = comment.get("id", "")
            msg = comment.get("message", "")
            sender_id = comment.get("from", {}).get("id", "")
            sub_comments = comment.get("comments", {}).get("data", [])
            already_done = any("[Afiliado]" in sc.get("message", "") for sc in sub_comments)
            if not cid or sender_id == page_id or "[Afiliado]" in msg or already_done:
                continue
            _, reply_text = build_reply_message(msg, tag, domain)
            if reply_text:
                reply_url = f"https://graph.facebook.com/v21.0/{urllib.parse.quote(cid)}/comments"
                _http_json(reply_url, method="POST", form={"message": reply_text, "access_token": token})
                replied += 1
    return replied


# --- 3. Instagram Graph API (Posts + Comment Replies + Direct Message Links) ---

def post_instagram_business(caption: str, image_url: str) -> dict | None:
    ig_id = os.getenv("IG_USER_ID", "")
    token = os.getenv("IG_ACCESS_TOKEN", "") or os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    if not (ig_id and token and image_url):
        return None
    base = f"https://graph.facebook.com/v21.0/{urllib.parse.quote(ig_id)}"
    container = _http_json(f"{base}/media", method="POST", form={"image_url": image_url, "caption": caption, "access_token": token})
    creation_id = container.get("id", "")
    if not creation_id:
        return None
    return _http_json(f"{base}/media_publish", method="POST", form={"creation_id": creation_id, "access_token": token})


def reply_instagram_comments(tag: str, domain: str) -> int:
    ig_id = os.getenv("IG_USER_ID", "")
    token = os.getenv("IG_ACCESS_TOKEN", "") or os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    if not (ig_id and token):
        return 0
    replied = 0
    media_url = f"https://graph.facebook.com/v21.0/{urllib.parse.quote(ig_id)}/media?fields=id,comments{{id,text,replies{{text}}}}&limit=5&access_token={urllib.parse.quote(token)}"
    data = _http_json(media_url)
    for media in data.get("data", []):
        for comment in media.get("comments", {}).get("data", []):
            cid = comment.get("id", "")
            text = comment.get("text", "")
            replies = comment.get("replies", {}).get("data", [])
            already_done = any("[Afiliado]" in r.get("text", "") for r in replies)
            if not cid or "[Afiliado]" in text or already_done:
                continue
            keyword, reply_text = build_reply_message(text, tag, domain)
            if reply_text:
                # 1. Public comment reply
                rep_url = f"https://graph.facebook.com/v21.0/{urllib.parse.quote(cid)}/replies"
                _http_json(rep_url, method="POST", form={"message": f"Enviei o link de '{keyword}' na sua DM e aqui: {reply_text}", "access_token": token})
                # 2. Private Reply DM with clickable link
                try:
                    dm_url = f"https://graph.facebook.com/v21.0/{urllib.parse.quote(ig_id)}/messages"
                    _http_json(
                        dm_url,
                        method="POST",
                        data={"recipient": {"comment_id": cid}, "message": {"text": reply_text}},
                        headers={"Authorization": f"Bearer {token}"},
                    )
                except Exception:
                    pass
                replied += 1
    return replied


def run_bot(publish_deal: bool = True, check_comments: bool = True) -> dict[str, int | str]:
    load_env()
    tag = os.getenv("AFFILIATE_TAG", "williamdevspe-20")
    domain = os.getenv("AMAZON_DOMAIN", "www.amazon.com.br")
    site_url = os.getenv("SITE_URL", "https://williamnext.github.io/auto-affiliate-seo")
    default_img = os.getenv("IG_PROMO_IMAGE_URL", "")

    deal = build_daily_deal_post(tag, domain, site_url)
    summary: dict[str, int | str] = {"deal_item": deal["name"], "fb_replies": 0, "ig_replies": 0}

    if publish_deal:
        try:
            if post_x_tweet(deal["text"]):
                summary["x_posted"] = 1
        except Exception as e:
            summary["x_error"] = str(e)[:120]
        try:
            if post_facebook_page(deal["text"], deal["url"]):
                summary["fb_posted"] = 1
        except Exception as e:
            summary["fb_error"] = str(e)[:120]
        try:
            if default_img and post_instagram_business(deal["text"], default_img):
                summary["ig_posted"] = 1
        except Exception as e:
            summary["ig_error"] = str(e)[:120]

    if check_comments:
        try:
            summary["fb_replies"] = reply_facebook_comments(tag, domain)
        except Exception as e:
            summary["fb_reply_error"] = str(e)[:120]
        try:
            summary["ig_replies"] = reply_instagram_comments(tag, domain)
        except Exception as e:
            summary["ig_reply_error"] = str(e)[:120]

    return summary


def self_check() -> None:
    assert extract_product_keyword("Oi! Quero comprar uma Airfryer Mondial 4L barata, me indica?") == "airfryer mondial 4l"
    assert extract_product_keyword("Tem promoção de fralda Pampers G hoje?") == "fralda pampers"
    assert extract_product_keyword("Me recomenda um fone bluetooth bom para corrida") == "fone bluetooth corrida"
    kw, msg = build_reply_message("Procuro um monitor gamer 144hz", tag="williamdevspe-20")
    assert kw == "monitor gamer 144hz"
    assert "https://www.amazon.com.br/s?k=monitor+gamer+144hz&tag=williamdevspe-20" in msg
    assert "[Afiliado]" in msg
    deal = build_daily_deal_post(tag="williamdevspe-20")
    assert "tag=williamdevspe-20" in deal["text"] and "#publi" in deal["text"]
    sig_hdr = _oauth1_header("POST", "https://api.twitter.com/2/tweets", "ck", "cs", "at", "ats", nonce="n1", ts="1700000000")
    assert 'oauth_signature="' in sig_hdr and sig_hdr.startswith("OAuth ")
    print("BOT SELF-CHECK PASSED: Keyword extraction, affiliate links, and OAuth1 verified.")


if __name__ == "__main__":
    if "--test" in sys.argv:
        self_check()
    else:
        only_comments = "--comments-only" in sys.argv
        result = run_bot(publish_deal=not only_comments, check_comments=True)
        print(json.dumps(result, ensure_ascii=False))
