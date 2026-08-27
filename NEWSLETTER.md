# Newsletter GTA 6 News — Mise en place

Envoi automatique quotidien des articles du jour à une liste d'abonnés, via l'API Brevo (gratuit jusqu'à 300 emails/jour, contacts illimités).

## Étape 1 — Créer un compte Brevo

1. Va sur **https://www.brevo.com**, clique "Sign up free"
2. Crée ton compte (aucune carte bancaire requise)
3. Vérifie ton adresse email

## Étape 2 — Vérifier ton adresse d'envoi

Brevo exige que l'adresse "expéditeur" soit vérifiée avant de pouvoir envoyer :
1. Dans Brevo : **Settings → Senders, Domains & Dedicated IPs → Senders**
2. Clique "Add a sender", entre ton adresse email (ex: ta propre adresse Gmail pour commencer)
3. Confirme via l'email de vérification reçu

*(Pour une meilleure délivrabilité à terme, tu pourras vérifier un domaine complet une fois que tu en auras un — pas obligatoire pour démarrer.)*

## Étape 3 — Créer la liste de contacts

1. Dans Brevo : **Contacts → Lists**
2. Clique "Create a list", nomme-la (ex: "GTA6 News Subscribers")
3. Une fois créée, **note l'ID numérique de la liste** (visible dans l'URL ou les détails de la liste — un nombre comme `3`)

## Étape 4 — Créer le formulaire d'inscription

1. Dans Brevo : **Contacts → Forms**
2. Clique "Create a form", associe-le à la liste créée à l'étape 3
3. Personnalise les champs si besoin (email suffit)
4. Une fois sauvegardé, Brevo te donne un **code d'intégration HTML** ("Embed on my website" ou similaire) — copie-le

## Étape 5 — Ajouter le formulaire à ton site

Ouvre `site/src/pages/index.astro` et colle le code d'intégration Brevo à l'endroit où tu veux que le formulaire apparaisse (par exemple juste après le `<header>`, avant `<main>`). Le code ressemble à un `<script>` ou un `<iframe>` fourni directement par Brevo — colle-le tel quel.

## Étape 6 — Récupérer ta clé API

1. Dans Brevo : clique sur ton profil (en haut à droite) → **SMTP & API**
2. Onglet **API Keys** → **Generate a new API key**
3. Copie la clé générée (elle ne sera plus affichée en entier après)

## Étape 7 — Configurer les secrets GitHub

Sur `github.com/TON_PSEUDO/gta6-watcher` → **Settings → Secrets and variables → Actions**, ajoute :

| Secret | Valeur |
|---|---|
| `BREVO_API_KEY` | La clé copiée à l'étape 6 |
| `BREVO_LIST_ID` | L'ID numérique noté à l'étape 3 |
| `BREVO_SENDER_EMAIL` | L'adresse vérifiée à l'étape 2 |
| `BREVO_SENDER_NAME` | Le nom affiché comme expéditeur, ex: `GTA 6 News` |
| `SITE_URL` | L'URL de ton site Vercel, ex: `https://gta6-watcher.vercel.app` |

## Étape 8 — Tester en local (optionnel mais recommandé)

```bash
set -a
source .env   # doit contenir les mêmes variables que ci-dessus, avec les préfixes BREVO_
set +a
python send_newsletter.py
```

Si tout est bien configuré, tu dois recevoir l'email sur ta propre adresse (si tu t'es toi-même inscrit à la liste pour tester).

## Étape 9 — Tester le workflow automatique

1. Sur GitHub : onglet **Actions** → **"GTA 6 Newsletter"** → **"Run workflow"**
2. Vérifie les logs : tu dois voir `[Newsletter] Campagne envoyée avec succès.`

Si tu vois `[Newsletter] Aucun article aujourd'hui, pas d'envoi.`, c'est normal si le watcher n'a rien trouvé de neuf ce jour précis — pas une erreur.

## Fréquence d'envoi

Le workflow est réglé pour tourner **une fois par jour à 18h UTC**. Pour changer l'heure, modifie la ligne `cron` dans `.github/workflows/newsletter.yml` (format : `minute heure * * *`, en UTC).

## Limite du plan gratuit Brevo

300 emails envoyés par jour, tous destinataires confondus. Concrètement : si tu as moins de 300 abonnés, une newsletter quotidienne passe sans problème. Au-delà de 300 abonnés, il faudra soit passer à un plan payant Brevo, soit réduire la fréquence d'envoi (par exemple hebdomadaire plutôt que quotidien).
