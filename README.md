# GTA 6 News Watcher

Pipeline automatique de veille GTA 6 : collecte des news (RSS + Reddit), déduplication, résumé par IA (Gemini), sortie prête à publier. Conçu pour tourner gratuitement sur GitHub Actions.

## Ce que ça fait

1. Interroge des flux RSS de sites d'actu jeux vidéo + Reddit
2. Filtre les articles qui mentionnent GTA 6
3. Ignore ceux déjà vus (base SQLite locale)
4. Envoie les nouveaux à l'API Gemini pour un résumé reformulé (pas de copie du texte source)
5. Sauvegarde le résultat en `.json` (intégration facile) et `.md` (lecture/publication rapide) dans `output/`

---

## Étape 1 — Récupérer une clé API Gemini (gratuit)

1. Va sur **https://aistudio.google.com/apikey**
2. Connecte-toi avec ton compte Google habituel (celui de Gemini Pro fonctionne, mais ça n'a aucun lien avec ton abonnement — c'est un accès API séparé et gratuit)
3. Clique sur **"Create API key"**
4. Copie la clé générée (elle commence par `AIza...`) — tu ne pourras plus la revoir en entier après, garde-la de côté

**Important** : avant de lancer le script, va sur **https://ai.google.dev/gemini-api/docs/pricing** et regarde la colonne "Free Tier" pour voir quel modèle Flash est actuellement gratuit (le nom change régulièrement, ex: `gemini-2.5-flash`, `gemini-3-flash`...). Note le nom exact, tu en auras besoin à l'étape 3.

## Étape 2 — Installer et tester en local

```bash
# Dans le dossier du projet
python -m venv venv
source venv/bin/activate      # sous Windows : venv\Scripts\activate

pip install -r requirements.txt
```

## Étape 3 — Configurer tes clés

```bash
cp .env.example .env
```

Ouvre le fichier `.env` et remplis :
```
GEMINI_API_KEY=AIza...          <- ta clé de l'étape 1
GEMINI_MODEL=gemini-2.5-flash   <- le nom exact noté à l'étape 1
```

(Laisse les lignes Reddit vides pour l'instant, elles sont optionnelles.)

## Étape 4 — Lancer un premier test

```bash
export $(cat .env | xargs)     # sous Windows, utilise plutôt python-dotenv
python watcher.py
```

Regarde dans le dossier `output/` : si des articles GTA 6 sont dans les flux RSS surveillés au moment du test, tu verras apparaître un fichier `.md` avec les résumés. S'il n'y a rien, c'est normal si aucun article récent ne correspond aux mots-clés — le script fonctionne quand même, il n'y a juste rien à traiter pour l'instant.

## Étape 5 — Automatiser avec GitHub Actions (gratuit, tourne tout seul)

1. Crée un compte GitHub si tu n'en as pas, puis un nouveau repository (privé ou public, peu importe)
2. Pousse tout le contenu de ce dossier dedans :
   ```bash
   git init
   git add .
   git commit -m "Premier commit du watcher"
   git branch -M main
   git remote add origin https://github.com/TON_PSEUDO/TON_REPO.git
   git push -u origin main
   ```
   *(Vérifie que `.env` n'est PAS poussé — un fichier `.gitignore` avec `.env` dedans est recommandé)*

3. Sur la page GitHub de ton repo : va dans **Settings → Secrets and variables → Actions → New repository secret**
4. Ajoute ces secrets un par un :
   - `GEMINI_API_KEY` → ta clé
   - `GEMINI_MODEL` → le nom du modèle (ex: `gemini-2.5-flash`)
   - (optionnel) `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`

5. Va dans l'onglet **Actions** de ton repo — le workflow "GTA 6 Watcher" doit apparaître. Clique dessus puis **"Run workflow"** pour le tester manuellement une première fois.

6. Si ça tourne sans erreur, c'est bon : il se relancera **automatiquement toutes les heures** tout seul, et les nouveaux articles seront commités dans le dossier `output/` de ton repo.

---

## Où récupérer les identifiants Reddit (optionnel)

Va sur **https://www.reddit.com/prefs/apps**, clique "create app", choisis le type "script". Tu obtiens un `client_id` (sous le nom de l'app) et un `client_secret`.

## Étape suivante : publication automatique

Ce pipeline produit la donnée (JSON/Markdown), il ne publie encore nulle part. Pour publier automatiquement :

- **Site statique (Astro/Next.js)** : ajoute une étape dans le workflow qui déclenche un build/déploiement (Vercel/Netlify) à chaque nouveau commit dans `output/`
- **Newsletter (Beehiiv/ConvertKit)** : ajoute un appel API à la fin de `watcher.py` qui envoie les nouveaux résumés du jour comme brouillon ou email

Dis-moi quand tu veux passer à cette étape, on branchera la publication.

## Ajuster la fréquence et les sources

- Fréquence : modifie la ligne `cron` dans `.github/workflows/watch.yml` (syntaxe cron standard, actuellement réglé sur toutes les heures)
- Sources RSS : ajoute/retire des entrées dans le dict `RSS_FEEDS` de `watcher.py`
- Mots-clés de filtrage : liste `KEYWORDS` dans `watcher.py`
- Subreddits : liste `SUBREDDITS` dans `watcher.py`

## Coût estimé

- GitHub Actions, hébergement, RSS, Reddit API : **0€**
- API Gemini (résumés) : **0€** avec le tier gratuit pour ce volume d'usage, tant que tu restes sous les quotas (vérifie-les sur la page pricing, ils évoluent)
- Nom de domaine (si tu passes à un vrai site) : ~10-15€/an, seul coût réel à prévoir plus tard

## Limites à connaître

- Les flux RSS peuvent changer d'URL ou de format sans prévenir — vérifie de temps en temps que `collect_rss()` remonte bien des résultats
- **Les tiers gratuits et noms de modèles Gemini changent régulièrement** (Google a déjà retiré des modèles du gratuit avec peu de préavis) — si le script commence à renvoyer des erreurs API, la première chose à vérifier est le nom du modèle dans `GEMINI_MODEL`
- Le filtrage par mots-clés est simple ; tu peux le rendre plus intelligent avec le temps si trop de faux positifs/négatifs
- Toujours citer et lier la source originale dans ta publication finale — c'est ce qui te protège légalement (tu rapportes un fait, tu ne republies pas un contenu)
