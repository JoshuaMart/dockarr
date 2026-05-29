<?php
// Static description of the stack: categories (ordered) and services (ordered).
// Status is probed at runtime against each service's internal health endpoint,
// exactly the ones the bootstrap uses (scripts/bootstrap/core/http.py).
//
// `optional` names a feature flag: the service is shown greyed and not probed
// unless that flag is on. Detection uses non-sensitive Compose variables passed
// as env (COMPOSE_PROFILES, COMPOSE_FILE), never .env or secrets/.

return [
    'categories' => [
        // key        => [fr, en]
        'download'   => ['Téléchargement', 'Downloads'],
        'indexers'   => ['Indexeurs', 'Indexers'],
        'media'      => ['Films & Séries', 'Movies & TV'],
        'profiles'   => ['Profils qualité', 'Quality profiles'],
        'requests'   => ['Demandes', 'Requests'],
        'library'    => ['Médiathèque', 'Media library'],
    ],

    'services' => [
        [
            'key' => 'qbittorrent', 'category' => 'download',
            'name' => 'qBittorrent', 'initials' => 'qB', 'color' => '#3a82c4',
            'host' => 'qbittorrent', 'port' => 8080, 'health' => '/',
            'subdomain' => 'qbittorrent',
            'desc' => ['Client BitTorrent', 'BitTorrent client'],
        ],
        [
            'key' => 'qui', 'category' => 'download',
            'name' => 'qui', 'initials' => 'qi', 'color' => '#16a394',
            'host' => 'qui', 'port' => 7476, 'health' => '/',
            'subdomain' => 'qui',
            'desc' => ['Interface web moderne pour qBittorrent', 'Modern qBittorrent web UI'],
        ],
        [
            'key' => 'prowlarr', 'category' => 'indexers',
            'name' => 'Prowlarr', 'initials' => 'P', 'color' => '#e8833a',
            'host' => 'prowlarr', 'port' => 9696, 'health' => '/api/v1/system/status',
            'subdomain' => 'prowlarr',
            'desc' => ["Gestionnaire d'indexeurs", 'Indexer manager'],
        ],
        [
            'key' => 'radarr', 'category' => 'media',
            'name' => 'Radarr', 'initials' => 'R', 'color' => '#e0bb3a',
            'host' => 'radarr', 'port' => 7878, 'health' => '/api/v3/system/status',
            'subdomain' => 'radarr',
            'desc' => ['Bibliothèque & suivi de films', 'Movie library & monitoring'],
        ],
        [
            'key' => 'sonarr', 'category' => 'media',
            'name' => 'Sonarr', 'initials' => 'S', 'color' => '#4a8fd8',
            'host' => 'sonarr', 'port' => 8989, 'health' => '/api/v3/system/status',
            'subdomain' => 'sonarr',
            'desc' => ['Bibliothèque & suivi de séries', 'TV library & monitoring'],
        ],
        [
            'key' => 'profilarr', 'category' => 'profiles',
            'name' => 'Profilarr', 'initials' => 'Pf', 'color' => '#8b5cf6',
            'host' => 'profilarr', 'port' => 6868, 'health' => '/api/v1/health',
            'subdomain' => 'profilarr',
            'desc' => ['Profils de qualité & custom formats', 'Quality profiles & custom formats'],
        ],
        [
            'key' => 'seerr', 'category' => 'requests',
            'name' => 'Seerr', 'initials' => 'Se', 'color' => '#6366f1',
            'host' => 'seerr', 'port' => 5055, 'health' => '/api/v1/status',
            'subdomain' => 'seerr',
            'desc' => ['Demandes de films & séries', 'Movie & TV requests'],
        ],
        [
            'key' => 'jellyfin', 'category' => 'library',
            'name' => 'Jellyfin', 'initials' => 'J', 'color' => '#9b59f0',
            'host' => 'jellyfin', 'port' => 8096, 'health' => '/System/Info/Public',
            'subdomain' => 'jellyfin',
            'desc' => ['Serveur de streaming vidéo', 'Video streaming server'],
        ],
        [
            'key' => 'kavita', 'category' => 'library',
            'name' => 'Kavita', 'initials' => 'K', 'color' => '#4db6ac',
            'host' => 'kavita', 'port' => 5000, 'health' => '/api/health',
            'subdomain' => 'kavita', 'optional' => 'kavita',
            'desc' => ['Lecture de BD, mangas & livres', 'Comics, manga & books reader'],
        ],
    ],
];
