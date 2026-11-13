# fab-meta

Site de fans (non commercial) sur la meta de **Flesh and Blood**, en commençant par le format **Silver Age**.

La page montre, depuis la dernière banlist, la part de la meta de chaque héros, ses victoires et ses tops 8, d'après les [decklists officielles de fabtcg.com](https://fabtcg.com/decklists/). Elle renvoie vers [fabtcgmeta](https://fabtcgmeta.com/), [Fablazing](https://fablazing.com/) et [FaBrary](https://fabrary.net/) pour les taux de victoire.

## Comment ça marche

Les résultats sont dans un simple tableau, `data/resultats.csv`, rempli à la main. À chaque modification, GitHub vérifie le fichier, recalcule les statistiques (`scripts/build_site.py`) et publie la page sur GitHub Pages. Rien à installer.

> Pourquoi pas de récupération automatique ? fabtcg.com refuse les requêtes automatiques (erreur 403) et ses conditions d'utilisation demandent un accord écrit pour reprendre son contenu. On pourra automatiser si Legend Story Studios ou un site de meta donne son accord.

## Mise en route (une seule fois)

1. Sur GitHub, ouvre le dépôt, puis **Settings** > **Pages**.
2. Dans **Build and deployment** > **Source**, choisis **GitHub Actions**.
3. Va dans l'onglet **Actions**, clique sur **Mettre à jour le site** puis **Run workflow**.
4. Après deux ou trois minutes, le site est visible à l'adresse `https://shuiloui.github.io/fab-meta/`.

## Ajouter des résultats

1. Sur GitHub, ouvre `data/resultats.csv` et clique sur l'icône crayon.
2. Ajoute une ligne par decklist, en recopiant les infos de [fabtcg.com/decklists](https://fabtcg.com/decklists/) :

| Colonne | Exemple | Remarque |
|---|---|---|
| `date` | `2026-11-08` | format AAAA-MM-JJ |
| `heros` | `"Ira, Crimson Haze"` | guillemets si le nom contient une virgule |
| `joueur` | `Davorin Pokorn` | |
| `tournoi` | `Sunday Showdown: Paris 2026` | |
| `place` | `1` | un nombre, ou vide si inconnue |
| `pays` | `Slovenia` | facultatif |
| `lien_decklist` | `https://fabtcg.com/decklists/...` | facultatif mais conseillé (source) |
| `lien_tournoi` | `https://fabtcg.com/...` | facultatif |

3. Clique sur **Commit changes**. Si une ligne est mal remplie, l'onglet Actions affiche une croix rouge avec le numéro de la ligne à corriger, et l'ancienne version du site reste en ligne.

## Après une nouvelle banlist

Ouvre `config.json` et change `since` (date de la banlist, AAAA-MM-JJ), `since_label`, `since_url` et `next_banlist`. Les résultats plus anciens restent dans le CSV mais ne sont plus comptés.

## Lancer en local (facultatif)

```bash
python3 scripts/build_site.py      # puis ouvrir site/index.html
python3 -m unittest discover tests
```

## Mentions

Flesh and Blood™ et tous les noms de cartes et de héros sont © Legend Story Studios. Ce site n'est ni affilié ni approuvé par Legend Story Studios. Chaque résultat renvoie vers sa source.
