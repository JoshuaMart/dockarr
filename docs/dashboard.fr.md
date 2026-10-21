# Dashboard

Une page d'accueil légère qui liste tous les services avec un statut **en ligne /
hors ligne** en direct et un lien vers leur interface. Elle est servie sur
`dashboard.${DOCKARR_DOMAIN}` (et sur le port hôte `8081` pour un accès direct).

![Dashboard](assets/banner.png)

## Fonctionnement

- **Stack** : PHP vanilla (`php:8.5-apache`) + une feuille de style écrite à la
  main + un peu de JavaScript vanilla. Ni framework, ni CDN, ni étape de build.
  Les thèmes clair et sombre suivent le réglage du système.
- **Statut = joignabilité uniquement** : une petite sonde côté serveur
  (`api/status.php`) interroge l'endpoint de santé interne de chaque service,
  les mêmes que ceux du bootstrap (ex. `/api/v3/system/status` pour
  Radarr/Sonarr, `/api/health` pour Kavita). Toute réponse HTTP inférieure à
  `500` compte comme **en ligne** (un `401` signifie que le serveur répond) ;
  une erreur de connexion ou un `5xx` signifie **hors ligne**.
- **Aucun secret, aucune clé API** : le dashboard ne monte jamais `.env` ni
  `secrets/`. Il reçoit seulement les valeurs non sensibles `COMPOSE_PROFILES`
  et `COMPOSE_FILE` en variables d'environnement pour savoir quels services
  optionnels sont actifs (Kavita, VPN), plus `DOCKARR_LANG` pour la langue.
- **Rafraîchissement auto** toutes les ~20 secondes, avec un bouton
  *Actualiser*. Chaque ligne garde un petit historique de latence des 12
  dernières vérifications (en mémoire : recharger la page le remet à zéro).

## Légende des statuts

| Indicateur | Signification |
| --- | --- |
| point neutre + latence | En ligne (joignable), avec le temps de réponse en ms |
| point orange, ligne teintée + « Hors ligne » | Hors ligne (connexion refusée, timeout ou 5xx) |
| tuile en pointillés + « Désactivé » | Service optionnel désactivé au `make install` |

L'interface reste volontairement en gris neutre : l'orange est le seul accent et
signale toujours qu'il y a quelque chose à regarder.

## Personnalisation

Les groupes (*Médias*, *Automatisation*, *Téléchargements*), la liste des
services, leurs descriptions et endpoints de santé sont dans
`dashboard/config.php`. Les libellés d'interface (FR/EN) sont dans
`dashboard/lib.php`. Modifiez ces fichiers pour ajouter un service ou changer un
texte.

!!! note "Badge VPN"
    Le badge VPN reflète si l'overlay VPN est activé (`COMPOSE_FILE`), pas un
    vrai contrôle du tunnel. Exposer l'API de contrôle de Gluetun permettrait
    d'afficher la vraie IP publique plus tard.
