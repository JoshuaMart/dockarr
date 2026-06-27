<?php
// Shared helpers: environment reading, optional-service detection, i18n.

function dash_lang(): string
{
    $lang = getenv('DOCKARR_LANG') ?: 'en';
    return $lang === 'fr' ? 'fr' : 'en';
}

function dash_domain(): string
{
    return getenv('DOCKARR_DOMAIN') ?: 'dockarr.local';
}

// Kavita lives behind the "kavita" Compose profile.
function dash_kavita_enabled(): bool
{
    $profiles = getenv('COMPOSE_PROFILES') ?: '';
    $list = array_filter(array_map('trim', explode(',', $profiles)));
    return in_array('kavita', $list, true);
}

// The VPN is on when the overlay file is layered via COMPOSE_FILE.
function dash_vpn_enabled(): bool
{
    $files = getenv('COMPOSE_FILE') ?: '';
    return str_contains($files, 'docker-compose.vpn.yml');
}

// Whether a service entry from config.php should be probed (vs shown greyed).
function dash_service_enabled(array $service): bool
{
    $flag = $service['optional'] ?? null;
    if ($flag === null) {
        return true;
    }
    if ($flag === 'kavita') {
        return dash_kavita_enabled();
    }
    return true;
}

// UI chrome strings. Service descriptions and category labels live in config.php.
function dash_strings(string $lang): array
{
    $fr = [
        'tagline'        => 'SELF-HOSTED MEDIA STACK',
        'online_word'    => 'en ligne',
        'online'         => 'En ligne',
        'offline'        => 'Hors ligne',
        'disabled'       => 'Désactivé',
        'offline_state'  => 'hors ligne',
        'disabled_state' => 'désactivé',
        'reachable'      => 'joignable',
        'all_good'       => 'Tous les services répondent',
        'vpn_on'         => 'VPN actif',
        'vpn_off'        => 'VPN inactif',
        'check'          => 'Vérifier',
        'next_check'     => 'Prochaine vérification dans',
        'seconds'        => 's',
        'always_on'      => 'toujours actif',
    ];
    $en = [
        'tagline'        => 'SELF-HOSTED MEDIA STACK',
        'online_word'    => 'online',
        'online'         => 'Online',
        'offline'        => 'Offline',
        'disabled'       => 'Disabled',
        'offline_state'  => 'offline',
        'disabled_state' => 'disabled',
        'reachable'      => 'reachable',
        'all_good'       => 'All services responding',
        'vpn_on'         => 'VPN active',
        'vpn_off'        => 'VPN inactive',
        'check'          => 'Refresh',
        'next_check'     => 'Next check in',
        'seconds'        => 's',
        'always_on'      => 'always on',
    ];
    return $lang === 'fr' ? $fr : $en;
}
