#!/usr/bin/env python3
"""
Script à lancer UNE FOIS après migration pour pré-configurer les flux RSS.
Usage : python3 init_rss.py
"""
 
from app import app
from core import db
from core.models import RssFeed
 
DEFAULT_FEEDS = [
    {
        "nom": "CERT-FR",
        "url": "https://www.cert.ssi.gouv.fr/feed/",
        "actif": False,
    },
    {
        "nom": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "actif": False,
    },
    {
        "nom": "Krebs on Security",
        "url": "https://krebsonsecurity.com/feed/",
        "actif": False,
    },
]
 
def init_rss():
    with app.app_context():
        db.create_all()
        for feed_data in DEFAULT_FEEDS:
            existing = RssFeed.query.filter_by(url=feed_data["url"]).first()
            if not existing:
                feed = RssFeed(**feed_data)
                db.session.add(feed)
                print(f"✅ Flux ajouté : {feed_data['nom']}")
            else:
                print(f"⚠️  Déjà présent : {feed_data['nom']}")
        db.session.commit()
        print("\n✅ Initialisation des flux RSS terminée.")
        print("   Activez-les depuis /admin/actualites")
 
if __name__ == "__main__":
    init_rss()