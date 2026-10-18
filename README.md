# Allure, coach semi-marathon

Appli web (à installer sur l’écran d’accueil de l’iPhone) qui affiche la séance du jour, la forme, le sommeil et le plan de préparation du semi d’Antony.

## Confidentialité

Les données Garmin ne sont jamais publiées en clair. Elles sont chiffrées dans `data.enc.json` (PBKDF2-SHA256, 600 000 itérations, puis AES-256-GCM) et déchiffrées uniquement dans le navigateur, avec une clé qui n’est pas dans ce dépôt.

## Mise à jour

Chaque matin, le check du coach régénère `data.enc.json` :

```
ALLURE_KEY='…' python3 tools/publish.py dossier_des_csv
```

## Installation sur iPhone

1. Ouvre le lien GitHub Pages du dépôt dans Safari.
2. Bouton Partager, puis « Sur l’écran d’accueil ».
3. Ouvre l’appli depuis l’icône et saisis la clé une seule fois.
