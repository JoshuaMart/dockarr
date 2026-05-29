# Dashboard

Une page d'accueil légère qui liste tous les services avec un statut **en ligne /
hors ligne** en direct et un lien vers leur interface. Elle est servie sur
`dashboard.${DOCKARR_DOMAIN}` (et sur le port hôte `8081` pour un accès direct).

![Dashboard](assets/banner.png)

## Fonctionnement

- **Stack** : PHP vanilla (`php:8.3-apache`) + [Pico.css](https://picocss.com)
  (vendorisé, sans CDN) + un peu de JavaScript vanilla. Aucune étape de build.
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
- **Rafraîchissement auto** toutes les ~20 secondes, avec un bouton *Vérifier*.

## Légende des statuts

| Indicateur | Signification |
| --- | --- |
| point vert + latence | En ligne (joignable), avec le temps de réponse en ms |
| point rouge + « hors ligne » | Hors ligne (connexion refusée, timeout ou 5xx) |
| point creux + « désactivé » | Service optionnel désactivé au `make install` |

## Personnalisation

La liste des services, leurs couleurs, descriptions et endpoints de santé sont
dans `dashboard/config.php`. Les libellés d'interface (FR/EN) sont dans
`dashboard/lib.php`. Modifiez ces fichiers pour ajouter une tuile ou changer un
texte.

!!! note "Badge VPN"
    Le badge VPN reflète si l'overlay VPN est activé (`COMPOSE_FILE`), pas un
    vrai contrôle du tunnel. Exposer l'API de contrôle de Gluetun permettrait
    d'afficher la vraie IP publique plus tard.
