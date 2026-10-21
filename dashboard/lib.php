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
// `{n}`, `{up}`, `{total}` and `{ms}` are filled in by assets/app.js.
function dash_strings(string $lang): array
{
    $fr = [
        'all_online'     => 'Tous les services sont en ligne',
        'one_down'       => '1 service ne répond pas',
        'many_down'      => '{n} services ne répondent pas',
        'checking'       => 'Vérification en cours…',
        'up_of_total'    => '{up} sur {total} en ligne',
        'disabled_state' => 'désactivé',
        'median'         => 'latence médiane {ms} ms',
        'no_response_1'  => 'aucune réponse à la dernière vérification',
        'no_response_n'  => 'aucune réponse aux {n} dernières vérifications',
        'offline'        => 'Hors ligne',
        'disabled'       => 'Désactivé',
        'vpn_on'         => 'VPN actif',
        'vpn_off'        => 'VPN inactif',
        'refresh'        => 'Actualiser',
        'next_check'     => 'Prochaine vérification dans',
        'seconds'        => 's',
        'footer'         => 'Sondé côté serveur, toutes les {n} s',
    ];
    $en = [
        'all_online'     => 'All services are online',
        'one_down'       => '1 service is not responding',
        'many_down'      => '{n} services are not responding',
        'checking'       => 'Checking…',
        'up_of_total'    => '{up} of {total} online',
        'disabled_state' => 'disabled',
        'median'         => 'median latency {ms} ms',
        'no_response_1'  => 'no response on the last check',
        'no_response_n'  => 'no response on the last {n} checks',
        'offline'        => 'Offline',
        'disabled'       => 'Disabled',
        'vpn_on'         => 'VPN active',
        'vpn_off'        => 'VPN inactive',
        'refresh'        => 'Refresh',
        'next_check'     => 'Next check in',
        'seconds'        => 's',
        'footer'         => 'Probed server-side, every {n} s',
    ];
    return $lang === 'fr' ? $fr : $en;
}
