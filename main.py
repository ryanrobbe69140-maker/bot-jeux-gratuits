import requests
import json
import os
from datetime import datetime

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
MEMOIRE_FILE = 'memoire.json'

# Mots-cles qui indiquent un acces temporaire (on ne veut PAS ca)
EXCLURE = ["free weekend", "free-to-play", "free to play", "trial", "beta", "demo", "playtest"]


def charger_memoire():
    if os.path.exists(MEMOIRE_FILE):
        with open(MEMOIRE_FILE, 'r') as f:
            return json.load(f)
    return {'deja_postes': []}


def sauvegarder_memoire(data):
    with open(MEMOIRE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def est_temporaire(offre):
    texte = (offre.get('title', '') + ' ' + offre.get('description', '')).lower()
    return any(mot in texte for mot in EXCLURE)


def poster_webhook(offre):
    payload = {
        "embeds": [{
            "title": f"🎁 {offre['title']}",
            "url": offre['open_giveaway_url'],
            "description": offre['description'][:300] + "...",
            "color": 65280,
            "image": {"url": offre['thumbnail']},
            "fields": [
                {"name": "Plateforme", "value": offre['platforms'], "inline": True},
                {"name": "Valeur d'origine", "value": offre['worth'], "inline": True},
                {"name": "Type", "value": offre.get('type', 'Game'), "inline": True}
            ],
            "footer": {"text": "Traqueur Automatisé - Trouvé via GamerPower"}
        }]
    }
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print(f"OK Message posté : {offre['title']}")
        return True
    else:
        print(f"Erreur webhook : {response.status_code}")
        return False


def verifier_offres():
    if not WEBHOOK_URL:
        print("Erreur : DISCORD_WEBHOOK_URL non trouvée")
        return

    memoire = charger_memoire()
    deja_postes = memoire['deja_postes']
    # type=game.loot.dlc remonte jeux + loot (skins, monnaie) + DLC
    url = "https://www.gamerpower.com/api/giveaways?type=game.loot.dlc&sort-by=date"

    try:
        reponse = requests.get(url, timeout=10)
        if reponse.status_code == 200:
            for offre in reversed(reponse.json()):
                if offre['id'] in deja_postes:
                    continue
                if est_temporaire(offre):
                    print(f"Ignoré (temporaire) : {offre['title']}")
                    deja_postes.append(offre['id'])  # noté pour pas re-tester chaque fois
                    continue
                poster_webhook(offre)
                deja_postes.append(offre['id'])

            memoire['deja_postes'] = deja_postes
            memoire['derniere_verification'] = datetime.now().isoformat()
            sauvegarder_memoire(memoire)
            print("Vérification terminée")
    except Exception as e:
        print(f"Erreur : {e}")


if __name__ == "__main__":
    verifier_offres()
