# fab-meta

Site de fans (non commercial) sur la meta de **Flesh and Blood**, en commençant par le format **Silver Age**.

La page montre, depuis la dernière banlist, la part de la meta de chaque héros, ses victoires et ses tops 8, d'après les [decklists officielles de fabtcg.com](https://fabtcg.com/decklists/). Elle renvoie vers [fabtcgmeta](https://fabtcgmeta.com/), [Fablazing](https://fablazing.com/) et [FaBrary](https://fabrary.net/) pour les taux de victoire.

## Comment ça marche

Chaque nuit, GitHub lance automatiquement deux petits scripts Python :

1. `scripts/fetch_decklists.py` lit le tableau des decklists sur fabtcg.com et garde celles du format Silver Age publiées depuis la date de `config.json`.
2. `scripts/build_site.py` calcule les statistiques et fabrique la page web dans le dossier `site/`.

Le site est ensuite publié sur GitHub Pages. Rien à installer, rien à lancer à la main.

## Mise en route (une seule fois)

1. Sur GitHub, ouvre le dépôt, puis **Settings** > **Pages**.
2. Dans **Build and deployment** > **Source**, choisis **GitHub Actions**.
3. Va dans l'onglet **Actions**, clique sur **Mettre à jour le site** puis **Run workflow**.
4. Après deux ou trois minutes, le site est visible à l'adresse `https://shuiloui.github.io/fab-meta/`.

## Après une nouvelle banlist

Ouvre `config.json` sur GitHub (icône crayon pour modifier) et change :

- `since` : la date de la nouvelle banlist, au format `AAAA-MM-JJ` ;
- `since_label` et `since_url` : le nom et le lien de l'annonce ;
- `next_banlist` : la date de la banlist suivante si elle est connue.

Enregistre (« Commit changes ») : le site se met à jour tout seul.

## Lancer en local (facultatif)

```bash
python3 scripts/fetch_decklists.py
python3 scripts/build_site.py
# puis ouvrir site/index.html dans un navigateur
python3 -m unittest discover tests   # tests, sans réseau
```

## Mentions

Flesh and Blood™ et tous les noms de cartes et de héros sont © Legend Story Studios. Ce site n'est ni affilié ni approuvé par Legend Story Studios. Chaque statistique renvoie vers sa source.
