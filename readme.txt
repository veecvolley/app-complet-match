# 🚀 Synthèse Globale du Projet : VEEC Scorer (Version Finale)

L'application **VEEC Scorer** est un outil de suivi de match interactif, construit avec **Python (Dash/Plotly)**, destiné à enregistrer le score, gérer les remplacements, suivre les temps morts, et visualiser la formation des équipes en temps réel sur un terrain de volleyball.

---

## I. 🛑 Défis de Conception et de Débogage Surmontés

Les points suivants représentent les difficultés les plus significatives rencontrées lors de la construction de l'application. Ils témoignent de choix d'architecture cruciaux et d'erreurs logiques corrigées.

### A. Gestion de l'État et Dépendances

* **Difficulté :** La nature réactive de Dash exige une **source de vérité unique (`dcc.Store`)**. Toute tentative de modifier l'état *en dehors* d'un `Output` de callback provoque une perte d'information.
* **Solution :** L'utilisation systématique de `copy.deepcopy(current_state)` au début de chaque callback pour garantir l'immuabilité de l'état initial avant modification.

### B. Problèmes de Sérialisation et Types de Données

* **Difficulté :** Le composant `dcc.Store` sérialise les données en JSON, ce qui convertit les clés numériques de dictionnaires (comme les positions `'1'` à `'6'`) en chaînes de caractères.
* **Solution :** Ajout de la fonction **`clean_formations(state)`** au début des callbacks principaux. Cette fonction force la reconversion des clés des positions en entiers (`int(k)`) pour maintenir la cohérence de la logique (ex: `formation_actuelle[1]` au lieu de `formation_actuelle['1']`).

### C. Complexité de la Logique Libero

* **Difficulté :** Gérer l'échange du Libero impliquait de suivre **trois joueurs simultanément** : le Libero Actif (N°8), le Libero Réserve (N°9), et le **Titulaire** remplacé (`starter_numero_replaced`), tout en respectant la règle de sortie forcée en P4.
* **Solution :** Création d'une structure d'état dédiée et détaillée (`liberos_veec`) et implémentation d'une logique de rotation Libero en deux temps :
    1.  Application de la rotation standard (`appliquer_rotation_veec`).
    2.  Vérification et exécution immédiate de la sortie forcée si le Libero est en P4.

---

## II. Architecture et Avancements

### A. Le Cœur de l'Application : L'Objet `initial_state`

Toute l'application repose sur le dictionnaire `initial_state`, qui contient l'état actuel de la partie, y compris la clé **`liberos_veec`** qui piste les deux Libéros et le joueur remplacé.

### B. Gestion de la Rotation Forcée (Règle P4)

* **Logique :** Implémentée dans `update_score_and_rotation`. Après une rotation, si le Libero est détecté en **Position 4** (zone avant), un échange automatique est forcé, sortant le Libero et réintroduisant le joueur titulaire (`starter_numero_replaced`).
* **Statut :** **Terminé** pour l'équipe VEEC.

### C. Rendu Graphique

* Le code dans `create_court_figure` est adapté pour lire `liberos_veec` et **colorier en jaune** le Libero (N°8 ou N°9) s'il est sur le terrain. 

[Image of volleyball court showing player positions]


---

## III. Points de Régression et Fonctionnalités à Débloquer

### A. 🔴 Régression Critique : Fenêtre de Statistiques

* **Problème :** La fenêtre modale ou le panneau affichant les **statistiques détaillées des joueurs ne s'ouvre plus**.
* **Tâche Prioritaire :** Déboguer le callback responsable de l'ouverture de la fenêtre (vérifier les `Input`/`State` et les propriétés `is_open` du `dcc.Modal`).

### B. Exportation de Données (Haute Priorité)

* **Fonctionnalité Requise :** Implémenter un mécanisme pour exporter l'ensemble des données du match (`historique_stats` et `final_state`) vers **Google Sheets (gSheet)**.

---

## IV. Prochaines Étapes et Fonctionnalités Recommandées

| Priorité | Fonctionnalité | Description et État |
| :--- | :--- | :--- |
| **P1** | **Réparation Stats Joueurs** | Déboguer et restaurer l'ouverture de la fenêtre de statistiques détaillées. |
| **P1** | **Exportation gSheet** | Implémenter le mécanisme d'exportation des données du match vers Google Sheets. |
| **P2** | **Gestion Libero Réserve (N°9)** | Implémenter la logique de substitution du Libero N°9 pour remplacer le Libero N°8. |
| **P3** | **Intégration Manuelle Libero** | Mettre à jour les Callbacks de substitution manuelle pour les Libéros. |
| **P4** | **Libero Adversaire** | Dupliquer toute la logique Libero pour l'équipe adverse. |

---

Que souhaitez-vous attaquer en premier : les deux nouvelles priorités (Réparation Stats ou Exportation gSheet) ou la finalisation du Libero (Échange N°9 ↔ N°8) ?
