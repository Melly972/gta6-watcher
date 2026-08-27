# GTA 6 News — Site

Site statique Astro qui affiche automatiquement les résumés générés par `watcher.py` (dossier `output/` un niveau au-dessus).

## Comment ça marche

À chaque build, la page lit tous les fichiers `../output/*.json`, les fusionne, les trie du plus récent au plus ancien, et génère une page HTML statique. Comme `watcher.py` tourne toutes les heures via GitHub Actions et pousse ses résultats dans `output/`, chaque nouveau commit déclenchera automatiquement un nouveau build du site une fois Vercel connecté (voir plus bas) — **aucune configuration supplémentaire nécessaire pour que le site se mette à jour tout seul**.

## Tester en local

```bash
cd site
npm install
npm run dev
```

Ouvre http://localhost:4321 — tu dois voir tes articles déjà générés par le watcher.

## Déployer sur Vercel (gratuit)

1. Va sur **vercel.com**, connecte-toi avec ton compte GitHub
2. Clique **"Add New" → "Project"**
3. Sélectionne ton repo `gta6-watcher`
4. **Étape cruciale** : dans "Configure Project", ouvre **"Root Directory"** et sélectionne le dossier **`site`** (pas la racine du repo — sinon Vercel ne trouvera pas le projet Astro)
5. Le "Framework Preset" devrait détecter automatiquement **Astro**
6. Clique **"Deploy"**

Après quelques secondes, Vercel te donne une URL (ex: `gta6-watcher.vercel.app`). Le site est en ligne.

## Mise à jour automatique

Comme le workflow `watch.yml` pousse un commit à chaque nouvel article trouvé, et que Vercel est connecté à ton repo GitHub, **chaque commit déclenche automatiquement un nouveau déploiement**. Tu n'as rien à faire de plus : le site se met à jour tout seul, en continu, sans aucune action manuelle.

## Nom de domaine personnalisé (optionnel, plus tard)

Une fois que tu veux un vrai nom de domaine (ex: `gta6-actu.fr`) :
1. Achète le domaine (Namecheap, OVH, etc. — environ 10-15€/an)
2. Dans Vercel : **Project Settings → Domains** → ajoute ton domaine
3. Suis les instructions pour configurer les DNS chez ton registrar

## Monétisation

Une fois que le site a du trafic régulier :
- **Google AdSense** : crée un compte sur adsense.google.com, ajoute ton site, attends la validation (peut prendre 1-2 semaines), puis insère le script fourni dans le `<head>` de `src/pages/index.astro`
- **Affiliation** : ajoute des liens Amazon Associates ou équivalent dans le contenu (pas encore intégré dans ce template, à faire quand tu es prêt)

## Personnalisation

- Couleurs/style : variables CSS en haut de `src/pages/index.astro` (`:root { --accent: ... }`)
- Nombre d'articles affichés : variable `displayedArticles = articles.slice(0, 60)` — change `60` selon ta préférence
- Titre/description : balises `<title>` et `<meta name="description">` dans le `<head>`
