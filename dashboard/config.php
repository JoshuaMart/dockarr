<?php
// Static description of the stack: categories (ordered) and services (ordered).
// The dashboard renders one panel per category, services in the order below.
// Status is probed at runtime against each service's internal health endpoint,
// exactly the ones the bootstrap uses (scripts/bootstrap/core/http.py).
//
// `optional` names a feature flag: the service is shown greyed and not probed
// unless that flag is on. Detection uses non-sensitive Compose variables passed
// as env (COMPOSE_PROFILES, COMPOSE_FILE), never .env or secrets/.

return [
    'categories' => [
        // key        => [fr, en]
        'media'      => ['Médias', 'Media'],
        'automation' => ['Automatisation', 'Automation'],
        'downloads'  => ['Téléchargements', 'Downloads'],
    ],

    'services' => [
        [
            'key' => 'jellyfin', 'category' => 'media',
            'name' => 'Jellyfin', 'initials' => 'J',
            'host' => 'jellyfin', 'port' => 8096, 'health' => '/System/Info/Public',
            'subdomain' => 'jellyfin',
            'desc' => ['Serveur de streaming vidéo', 'Video streaming server'],
        ],
        [
            'key' => 'seerr', 'category' => 'media',
            'name' => 'Seerr', 'initials' => 'Se',
            'host' => 'seerr', 'port' => 5055, 'health' => '/api/v1/status',
            'subdomain' => 'seerr',
            'desc' => ['Demandes de films & séries', 'Movie & TV requests'],
        ],
        [
            'key' => 'kavita', 'category' => 'media',
            'name' => 'Kavita', 'initials' => 'K',
            'host' => 'kavita', 'port' => 5000, 'health' => '/api/health',
            'subdomain' => 'kavita', 'optional' => 'kavita',
            'desc' => ['Lecture de BD, mangas & livres', 'Comics, manga & books reader'],
        ],
        [
            'key' => 'radarr', 'category' => 'automation',
            'name' => 'Radarr', 'initials' => 'R',
            'host' => 'radarr', 'port' => 7878, 'health' => '/api/v3/system/status',
            'subdomain' => 'radarr',
            'desc' => ['Bibliothèque & suivi de films', 'Movie library & monitoring'],
        ],
        [
            'key' => 'sonarr', 'category' => 'automation',
            'name' => 'Sonarr', 'initials' => 'S',
            'host' => 'sonarr', 'port' => 8989, 'health' => '/api/v3/system/status',
            'subdomain' => 'sonarr',
            'desc' => ['Bibliothèque & suivi de séries', 'TV library & monitoring'],
        ],
        [
            'key' => 'prowlarr', 'category' => 'automation',
            'name' => 'Prowlarr', 'initials' => 'P',
            'host' => 'prowlarr', 'port' => 9696, 'health' => '/api/v1/system/status',
            'subdomain' => 'prowlarr',
            'desc' => ["Gestionnaire d'indexeurs", 'Indexer manager'],
        ],
        [
            'key' => 'profilarr', 'category' => 'automation',
            'name' => 'Profilarr', 'initials' => 'Pf',
            'host' => 'profilarr', 'port' => 6868, 'health' => '/api/v1/health',
            'subdomain' => 'profilarr',
            'desc' => ['Profils de qualité & custom formats', 'Quality profiles & custom formats'],
        ],
        [
            'key' => 'qbittorrent', 'category' => 'downloads',
            'name' => 'qBittorrent', 'initials' => 'qB',
            'host' => 'qbittorrent', 'port' => 8080, 'health' => '/',
            'subdomain' => 'qbittorrent',
            'desc' => ['Client BitTorrent', 'BitTorrent client'],
        ],
        [
            'key' => 'qui', 'category' => 'downloads',
            'name' => 'qui', 'initials' => 'qi',
            'host' => 'qui', 'port' => 7476, 'health' => '/',
            'subdomain' => 'qui',
            'desc' => ['Interface web moderne pour qBittorrent', 'Modern qBittorrent web UI'],
        ],
    ],
];
