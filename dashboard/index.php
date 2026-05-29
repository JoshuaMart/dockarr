<?php
require __DIR__ . '/lib.php';
$config = require __DIR__ . '/config.php';

$lang = dash_lang();
$domain = dash_domain();
$s = dash_strings($lang);
$vpn = dash_vpn_enabled();

$categories = $config['categories'];
$services = $config['services'];

// Group services by category, preserving both orders.
$byCat = [];
foreach ($services as $svc) {
    $byCat[$svc['category']][] = $svc;
}

$order = array_column($services, 'key');
$jsConfig = [
    'refreshSeconds' => 20,
    'order' => $order,
    'strings' => $s,
];

function e(string $v): string
{
    return htmlspecialchars($v, ENT_QUOTES, 'UTF-8');
}
?>
<!DOCTYPE html>
<html lang="<?= e($lang) ?>" data-theme="dark">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Dockarr</title>
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%2318b6a0'/%3E%3Ctext x='32' y='45' font-size='40' font-family='sans-serif' font-weight='bold' text-anchor='middle' fill='%23043'%3ED%3C/text%3E%3C/svg%3E">
    <link rel="stylesheet" href="assets/pico.min.css">
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
<main class="container">

    <header class="topbar">
        <div class="brand">
            <div class="brand-logo">D</div>
            <div class="brand-text">
                <h1>Dock<span>arr</span></h1>
                <p><?= e($s['tagline']) ?></p>
            </div>
        </div>
        <div class="controls">
            <span id="vpn-badge" class="badge <?= $vpn ? 'is-on' : 'is-off' ?>">
                <span class="dot"></span>
                <span class="label"><?= e($vpn ? $s['vpn_on'] : $s['vpn_off']) ?></span>
            </span>
            <span id="clock" class="clock">--:--:--</span>
            <button id="refresh" class="refresh" type="button">
                <span class="ico">&#x21bb;</span> <?= e($s['check']) ?>
            </button>
        </div>
    </header>

    <section class="summary">
        <div class="summary-main">
            <div class="headline">
                <span id="online-count">–</span><span class="sep">/</span><span id="total-count">–</span>
                <span class="headline-word"><?= e($s['online_word']) ?></span>
            </div>
            <div id="subtitle" class="subtitle"></div>
        </div>
        <div class="summary-side">
            <div id="segments" class="segments" aria-hidden="true"></div>
            <div class="legend">
                <span><span class="dot up"></span><?= e($s['online']) ?></span>
                <span><span class="dot down"></span><?= e($s['offline']) ?></span>
                <span><span class="dot off"></span><?= e($s['disabled']) ?></span>
            </div>
            <div class="next-check">
                <?= e($s['next_check']) ?> <span id="countdown">–</span> <?= e($s['seconds']) ?>
            </div>
        </div>
    </section>

    <?php foreach ($categories as $catKey => $labels): ?>
        <?php if (empty($byCat[$catKey])) continue; ?>
        <?php $label = $lang === 'fr' ? $labels[0] : $labels[1]; ?>
        <section class="group">
            <div class="group-head">
                <h2><?= e($label) ?></h2>
                <span class="group-count"><?= count($byCat[$catKey]) ?></span>
            </div>
            <div class="cards">
                <?php foreach ($byCat[$catKey] as $svc): ?>
                    <?php
                    $enabled = dash_service_enabled($svc);
                    $url = "https://{$svc['subdomain']}.{$domain}";
                    $desc = $lang === 'fr' ? $svc['desc'][0] : $svc['desc'][1];
                    ?>
                    <article class="card<?= $enabled ? '' : ' is-disabled' ?>" data-key="<?= e($svc['key']) ?>">
                        <div class="card-icon" style="--c: <?= e($svc['color']) ?>"><?= e($svc['initials']) ?></div>
                        <div class="card-body">
                            <?php if ($enabled): ?>
                                <a class="card-name" href="<?= e($url) ?>" target="_blank" rel="noopener"><?= e($svc['name']) ?></a>
                            <?php else: ?>
                                <span class="card-name"><?= e($svc['name']) ?></span>
                            <?php endif; ?>
                            <p class="card-desc"><?= e($desc) ?></p>
                        </div>
                        <div class="card-status" data-state="pending">
                            <span class="latency"></span>
                            <span class="dot"></span>
                        </div>
                    </article>
                <?php endforeach; ?>
            </div>
        </section>
    <?php endforeach; ?>

    <footer class="footer">
        <span>dashboard.<?= e($domain) ?> · <?= e($s['always_on']) ?></span>
        <span><?= e($s['footer_note']) ?></span>
    </footer>

</main>

<script>window.DASHBOARD = <?= json_encode($jsConfig, JSON_UNESCAPED_UNICODE) ?>;</script>
<script src="assets/app.js"></script>
</body>
</html>
