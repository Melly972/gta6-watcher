#!/usr/bin/env python3
"""
GTA 6 News Watcher
-------------------
Pipeline : collecte (RSS + Reddit) -> dédup -> résumé IA -> sortie JSON/Markdown

Usage :
    python watcher.py

Variables d'environnement requises (voir .env.example) :
    GEMINI_API_KEY      - clé API Google Gemini (AI Studio) pour le résumé
    GEMINI_MODEL        - (optionnel) nom du modèle, ex: gemini-2.5-flash
    REDDIT_CLIENT_ID    - (optionnel) pour activer la collecte Reddit
    REDDIT_CLIENT_SECRET
    REDDIT_USER_AGENT
"""

import os
import re
import json
import sqlite3
import hashlib
import datetime
from pathlib import Path

import feedparser
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent
DB_PATH = ROOT / "seen_articles.db"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Flux RSS à surveiller. Ajoute/retire librement.
RSS_FEEDS = {
    "IGN": "https://www.ign.com/rss/articles/feed",
    "GameSpot": "https://www.gamespot.com/feeds/news/",
    "Eurogamer": "https://www.eurogamer.net/feed",
    "PCGamer": "https://www.pcgamer.com/rss/",
    "RockPaperShotgun": "https://www.rockpapershotgun.com/feed",
}

# Mots-clés pour filtrer le bruit (insensible à la casse)
KEYWORDS = [
    "gta 6", "gta vi", "grand theft auto vi", "grand theft auto 6",
    "rockstar games", "take-two", "vice city"
]

# Subreddits à surveiller (nécessite les identifiants Reddit API)
SUBREDDITS = ["GTA6", "GamingLeaksAndRumours"]

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# Nom du modèle configurable : Google change régulièrement les modèles
# éligibles au tier gratuit. Vérifie le nom exact et actuel sur
# https://ai.google.dev/gemini-api/docs/pricing (colonne "Free Tier")
# avant de lancer, et ajuste GEMINI_MODEL dans ton .env si besoin.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

SUMMARY_PROMPT = """Tu es un rédacteur d'actualités jeux vidéo. Voici un article source sur GTA 6.

Rédige un résumé de 3-4 phrases MAXIMUM qui :
- reformule intégralement l'information avec tes propres mots (ne recopie AUCUNE phrase de la source)
- reste factuel et neutre, sans opinion
- va à l'essentiel : qui a dit quoi, quelle est la nouvelle information

Titre source : {title}
Contenu source : {content}

Réponds uniquement avec le résumé, sans préambule ni formule d'introduction."""


# ---------------------------------------------------------------------------
# Base de données (dédup)
# ---------------------------------------------------------------------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen (
            hash TEXT PRIMARY KEY,
            source TEXT,
            title TEXT,
            url TEXT,
            first_seen TEXT
        )
    """)
    conn.commit()
    return conn


def article_hash(url: str, title: str) -> str:
    return hashlib.sha256(f"{url}|{title}".encode("utf-8")).hexdigest()


def is_new(conn, url: str, title: str) -> bool:
    h = article_hash(url, title)
    cur = conn.execute("SELECT 1 FROM seen WHERE hash = ?", (h,))
    return cur.fetchone() is None


def mark_seen(conn, url: str, title: str, source: str):
    h = article_hash(url, title)
    conn.execute(
        "INSERT OR IGNORE INTO seen (hash, source, title, url, first_seen) VALUES (?, ?, ?, ?, ?)",
        (h, source, title, url, datetime.datetime.utcnow().isoformat())
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Filtrage
# ---------------------------------------------------------------------------

def matches_keywords(text: str) -> bool:
    text_low = text.lower()
    return any(kw in text_low for kw in KEYWORDS)


# ---------------------------------------------------------------------------
# Collecte RSS
# ---------------------------------------------------------------------------

def collect_rss():
    items = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[RSS] Erreur sur {source}: {e}")
            continue

        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            link = entry.get("link", "")

            if matches_keywords(title + " " + summary):
                items.append({
                    "source": source,
                    "title": title,
                    "content": re.sub("<[^<]+?>", "", summary),  # strip HTML basique
                    "url": link,
                })
    return items


# ---------------------------------------------------------------------------
# Collecte Reddit (optionnelle, nécessite praw + identifiants)
# ---------------------------------------------------------------------------

def collect_reddit():
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "gta6-watcher/0.1")

    if not client_id or not client_secret:
        print("[Reddit] Identifiants absents, collecte Reddit ignorée.")
        return []

    try:
        import praw
    except ImportError:
        print("[Reddit] praw non installé (pip install praw). Collecte ignorée.")
        return []

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )

    items = []
    for sub_name in SUBREDDITS:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.hot(limit=25):
                if post.score < 50:  # filtre le bruit à faible engagement
                    continue
                items.append({
                    "source": f"r/{sub_name}",
                    "title": post.title,
                    "content": (post.selftext or post.title)[:1500],
                    "url": f"https://reddit.com{post.permalink}",
                })
        except Exception as e:
            print(f"[Reddit] Erreur sur r/{sub_name}: {e}")

    return items


# ---------------------------------------------------------------------------
# Résumé via API Anthropic
# ---------------------------------------------------------------------------

def summarize(title: str, content: str) -> str:
    if not GEMINI_API_KEY:
        # Fallback sans IA si pas de clé configurée : renvoie le contenu tronqué
        return content[:280] + ("..." if len(content) > 280 else "")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

    try:
        response = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            headers={"content-type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": SUMMARY_PROMPT.format(title=title, content=content[:2000])}
                        ]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 300,
                    "temperature": 0.3,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[Résumé] Erreur API: {e}")
        return content[:280] + ("..." if len(content) > 280 else "")


# ---------------------------------------------------------------------------
# Sortie (JSON + Markdown)
# ---------------------------------------------------------------------------

def save_results(results: list):
    if not results:
        print("Aucun nouvel article.")
        return

    today = datetime.date.today().isoformat()

    # JSON (pour intégration site/newsletter)
    json_path = OUTPUT_DIR / f"{today}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Markdown lisible (pour vérif manuelle ou publication rapide)
    md_path = OUTPUT_DIR / f"{today}.md"
    with open(md_path, "a", encoding="utf-8") as f:
        for item in results:
            f.write(f"## {item['title']}\n")
            f.write(f"*Source : {item['source']}*\n\n")
            f.write(f"{item['summary']}\n\n")
            f.write(f"[Lire l'article original]({item['url']})\n\n---\n\n")

    print(f"{len(results)} nouvel(le)(s) article(s) sauvegardé(s) dans {json_path.name} et {md_path.name}")


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def main():
    conn = init_db()
    raw_items = collect_rss() + collect_reddit()

    new_results = []
    for item in raw_items:
        if not is_new(conn, item["url"], item["title"]):
            continue

        summary = summarize(item["title"], item["content"])
        new_results.append({
            "source": item["source"],
            "title": item["title"],
            "summary": summary,
            "url": item["url"],
            "date": datetime.datetime.utcnow().isoformat(),
        })
        mark_seen(conn, item["url"], item["title"], item["source"])

    save_results(new_results)
    conn.close()


if __name__ == "__main__":
    main()
