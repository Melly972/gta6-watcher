#!/usr/bin/env python3
"""
GTA 6 Newsletter Sender
------------------------
Compile les articles du jour (générés par watcher.py) en un email HTML
et l'envoie via l'API Brevo à la liste d'abonnés.

Usage :
    python send_newsletter.py

Variables d'environnement requises :
    BREVO_API_KEY      - clé API Brevo
    BREVO_LIST_ID       - ID numérique de la liste de contacts Brevo
    BREVO_SENDER_EMAIL  - email expéditeur (doit être vérifié dans Brevo)
    BREVO_SENDER_NAME   - (optionnel) nom affiché comme expéditeur
    SITE_URL            - (optionnel) URL du site pour le lien "voir en ligne"
"""

import os
import json
import glob
import datetime
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(ROOT, "output")

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_LIST_ID = os.environ.get("BREVO_LIST_ID", "")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "")
BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "GTA 6 News")
SITE_URL = os.environ.get("SITE_URL", "")


def load_today_articles():
    """Charge les articles du fichier JSON du jour, s'il existe."""
    today = datetime.date.today().isoformat()
    path = os.path.join(OUTPUT_DIR, f"{today}.json")

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_html_email(articles: list) -> str:
    """Construit le contenu HTML de l'email à partir des articles."""
    items_html = ""
    for a in articles:
        items_html += f"""
        <tr>
          <td style="padding: 16px 0; border-bottom: 1px solid #2a2a30;">
            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: #ff6b35; font-weight: 600; margin-bottom: 6px;">
              {a['source']}
            </div>
            <div style="font-size: 16px; font-weight: 600; color: #17171b; margin-bottom: 8px; line-height: 1.4;">
              {a['title']}
            </div>
            <div style="font-size: 14px; color: #444; line-height: 1.5; margin-bottom: 8px;">
              {a['summary']}
            </div>
            <a href="{a['url']}" style="font-size: 13px; color: #ff6b35; text-decoration: none;">
              Lire l'article original &rarr;
            </a>
          </td>
        </tr>
        """

    site_link = (
        f'<p style="text-align:center; margin-top: 24px;"><a href="{SITE_URL}" style="color:#ff6b35; font-size: 13px;">Voir toute l\'actualité sur le site &rarr;</a></p>'
        if SITE_URL else ""
    )

    return f"""
    <html>
    <body style="margin:0; padding:0; background:#f4f4f5; font-family: -apple-system, Arial, sans-serif;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5; padding: 24px 0;">
        <tr>
          <td align="center">
            <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius: 10px; overflow:hidden;">
              <tr>
                <td style="padding: 28px 32px 8px;">
                  <h1 style="font-size: 22px; margin:0; color:#17171b;">GTA 6 <span style="color:#ff6b35;">News</span></h1>
                  <p style="font-size: 13px; color:#888; margin: 4px 0 0;">Le récap du jour — {datetime.date.today().strftime('%d %B %Y')}</p>
                </td>
              </tr>
              <tr>
                <td style="padding: 8px 32px 24px;">
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                    {items_html}
                  </table>
                  {site_link}
                </td>
              </tr>
              <tr>
                <td style="padding: 16px 32px; background:#f4f4f5; text-align:center;">
                  <p style="font-size: 11px; color:#999; margin:0;">
                    Site indépendant non affilié à Rockstar Games ou Take-Two Interactive.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """


def send_campaign(html_content: str, article_count: int) -> bool:
    """Crée et envoie immédiatement une campagne Brevo à la liste configurée."""
    if not all([BREVO_API_KEY, BREVO_LIST_ID, BREVO_SENDER_EMAIL]):
        print("[Newsletter] Configuration Brevo incomplète (clé, liste ou expéditeur manquant). Envoi annulé.")
        return False

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    today_str = datetime.date.today().strftime("%d/%m/%Y")

    create_payload = {
        "name": f"GTA 6 News - {today_str}",
        "subject": f"🎮 GTA 6 News — {article_count} nouvel(le)(s) info(s) aujourd'hui",
        "sender": {"name": BREVO_SENDER_NAME, "email": BREVO_SENDER_EMAIL},
        "type": "classic",
        "htmlContent": html_content,
        "recipients": {"listIds": [int(BREVO_LIST_ID)]},
    }

    resp = requests.post(
        "https://api.brevo.com/v3/emailCampaigns",
        headers=headers,
        json=create_payload,
        timeout=30,
    )

    if resp.status_code not in (200, 201):
        print(f"[Newsletter] Erreur création campagne: {resp.status_code} {resp.text}")
        return False

    campaign_id = resp.json().get("id")
    print(f"[Newsletter] Campagne créée (id={campaign_id}), envoi en cours...")

    send_resp = requests.post(
        f"https://api.brevo.com/v3/emailCampaigns/{campaign_id}/sendNow",
        headers=headers,
        timeout=30,
    )

    if send_resp.status_code in (200, 201, 204):
        print("[Newsletter] Campagne envoyée avec succès.")
        return True
    else:
        print(f"[Newsletter] Erreur envoi campagne: {send_resp.status_code} {send_resp.text}")
        return False


def main():
    articles = load_today_articles()

    if not articles:
        print("[Newsletter] Aucun article aujourd'hui, pas d'envoi.")
        return

    html = build_html_email(articles)
    send_campaign(html, len(articles))


if __name__ == "__main__":
    main()
