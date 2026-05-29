<?php
// Server-side reachability probe. Returns JSON describing each service's state
// so the browser never talks to internal containers directly (no CORS, no
// internal URLs exposed). Mirrors the bootstrap's rule: any HTTP response < 500
// means "up"; a connection error or 5xx means "down".

require __DIR__ . '/../lib.php';
$config = require __DIR__ . '/../config.php';

header('Content-Type: application/json');
header('Cache-Control: no-store');

$services = $config['services'];
$order = array_column($services, 'key');

// Probe all enabled services in parallel.
$mh = curl_multi_init();
$handles = [];
$result = [];

foreach ($services as $svc) {
    if (!dash_service_enabled($svc)) {
        $result[$svc['key']] = ['state' => 'disabled', 'ms' => null];
        continue;
    }
    $url = "http://{$svc['host']}:{$svc['port']}{$svc['health']}";
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_NOBODY         => false,
        CURLOPT_CONNECTTIMEOUT => 2,
        CURLOPT_TIMEOUT        => 3,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_USERAGENT      => 'dockarr-dashboard',
    ]);
    curl_multi_add_handle($mh, $ch);
    $handles[$svc['key']] = $ch;
}

if ($handles) {
    do {
        $status = curl_multi_exec($mh, $running);
        if ($running) {
            curl_multi_select($mh, 1.0);
        }
    } while ($running && $status === CURLM_OK);

    foreach ($handles as $key => $ch) {
        $code = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        $ms = (int) round(curl_getinfo($ch, CURLINFO_TOTAL_TIME) * 1000);
        $up = curl_errno($ch) === 0 && $code > 0 && $code < 500;
        $result[$key] = ['state' => $up ? 'up' : 'down', 'ms' => $up ? $ms : null];
        curl_multi_remove_handle($mh, $ch);
    }
}
curl_multi_close($mh);

// Preserve config order.
$ordered = [];
foreach ($order as $key) {
    $ordered[$key] = $result[$key];
}

echo json_encode([
    'services' => $ordered,
    'vpn'      => dash_vpn_enabled(),
]);
