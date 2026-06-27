import requests
import json
import os
from datetime import datetime

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
MEMOIRE_FILE = 'memoire.json'

# Mots-cles qui indiquent un acces temporaire (on ne veut PAS ca)
EXCLURE = ["free weekend", "free-to-play", "free to play", "trial", "beta", "demo", "playtest"]

# En-tete "navigateur" : certains sites refusent les requetes sans User-Agent.
# On se fait passer pour un Chrome normal pour eviter d'etre bloque.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def charger_memoire():
    if os.path.exists(MEMOIRE_FILE):
        with open(MEMOIRE_FILE, 'r') as f:
            return json.load(f)
    return {'deja_postes': []}


def sauvegarder_memoire(data):
    with open(MEMOIRE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def est_temporaire(offre):
    # (offre.get(...) or '') protege le cas ou le champ est vide (None)
    texte = ((offre.get('title') or '') + ' ' + (offre.get('description') or '')).lower()
    return any(mot in texte for mot in EXCLURE)


def poster_webhook(offre):
    description = (offre.get('description') or '')[:300]
    payload = {
        "embeds": [{
            "title": f"🎁 {offre.get('title', 'Sans titre')}",
            "url": offre.get('open_giveaway_url', ''),
            "description": description + "...",
            "color": 65280,
            "image": {"url": offre.get('thumbnail', '')},
            "fields": [
                {"name": "Plateforme", "value": offre.get('platforms', 'N/A'), "inline": True},
                {"name": "Valeur d'origine", "value": offre.get('worth', 'N/A'), "inline": True},
                {"name": "Type", "value": offre.get('type', 'Game'), "inline": True}
            ],
            "footer": {"text": "Traqueur Automatisé - Trouvé via GamerPower"}
        }]
    }
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print(f"OK Message posté : {offre.get('title')}")
        return True
    else:
        print(f"Erreur webhook : {response.status_code} - {response.text[:200]}")
        return False


def verifier_offres():
    if not WEBHOOK_URL:
        print("Erreur : DISCORD_WEBHOOK_URL non trouvée")
        raise SystemExit(1)

    memoire = charger_memoire()
    deja_postes = memoire['deja_postes']
    # URL corrigee : type=game (valeur valide et documentee chez GamerPower)
    url = "https://www.gamerpower.com/api/giveaways?type=game&sort-by=date"

    reponse = requests.get(url, headers=HEADERS, timeout=20)

    # >>> La ligne la plus importante : on AFFICHE ce que GamerPower repond <<<
    print(f"Statut HTTP GamerPower : {reponse.status_code}")

    if reponse.status_code != 200:
        print(f"Reponse inattendue (200 attendu). Debut du corps : {reponse.text[:300]}")
        raise SystemExit(1)  # plante en ROUGE pour qu'on voie le probleme

    try:
        offres = reponse.json()
    except Exception as e:
        print(f"La reponse n'est pas du JSON : {e}. Debut du corps : {reponse.text[:300]}")
        raise SystemExit(1)

    if not isinstance(offres, list):
        print(f"JSON inattendu (une liste etait attendue). Recu : {str(offres)[:300]}")
        raise SystemExit(1)

    print(f"{len(offres)} offres reçues de GamerPower. {len(deja_postes)} deja connues.")

    nouvelles = 0
    for offre in reversed(offres):
        oid = offre.get('id')
        if oid is None or oid in deja_postes:
            continue
        if est_temporaire(offre):
            print(f"Ignoré (temporaire) : {offre.get('title')}")
            deja_postes.append(oid)
            continue
        poster_webhook(offre)
        deja_postes.append(oid)
        nouvelles += 1

    memoire['deja_postes'] = deja_postes
    memoire['derniere_verification'] = datetime.now().isoformat()
    sauvegarder_memoire(memoire)
    print(f"Vérification terminée. {nouvelles} nouvelle(s) offre(s) postée(s).")


if __name__ == "__main__":
    verifier_offres()
