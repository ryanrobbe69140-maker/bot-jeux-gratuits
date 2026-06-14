import requests
import json
import os
from datetime import datetime

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
MEMOIRE_FILE = 'memoire.json'


def charger_memoire():
    if os.path.exists(MEMOIRE_FILE):
        with open(MEMOIRE_FILE, 'r') as f:
            return json.load(f)
    return {'deja_postes': []}


def sauvegarder_memoire(data):
    with open(MEMOIRE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def poster_webhook(titre, url, description, plateforme, valeur, thumbnail):
    payload = {
        "embeds": [{
            "title": f"🎁 {titre}",
            "url": url,
            "description": description[:300] + "...",
            "color": 65280,
            "image": {"url": thumbnail},
            "fields": [
                {"name": "Plateforme", "value": plateforme, "inline": True},
                {"name": "Valeur d'origine", "value": valeur, "inline": True}
            ],
            "footer": {"text": "Traqueur Automatisé - Trouvé via GamerPower"}
        }]
    }
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print(f"OK Message posté : {titre}")
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
    url = "https://www.gamerpower.com/api/giveaways?type=game&sort-by=date"

    try:
        reponse = requests.get(url, timeout=10)
        if reponse.status_code == 200:
            # On prend TOUTES les offres, plus de limite [:5]
            # On lit de la plus ancienne a la plus recente pour un ordre logique dans le chat
            for offre in reversed(reponse.json()):
                if offre['id'] not in deja_postes:
                    poster_webhook(offre['title'], offre['open_giveaway_url'],
                                   offre['description'], offre['platforms'],
                                   offre['worth'], offre['thumbnail'])
                    deja_postes.append(offre['id'])

            memoire['deja_postes'] = deja_postes
            memoire['derniere_verification'] = datetime.now().isoformat()
            sauvegarder_memoire(memoire)
            print("Vérification terminée")
    except Exception as e:
        print(f"Erreur : {e}")


if __name__ == "__main__":
    verifier_offres()
