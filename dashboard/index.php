<?php
require __DIR__ . '/lib.php';
$config = require __DIR__ . '/config.php';

$lang = dash_lang();
$domain = dash_domain();
$s = dash_strings($lang);
$vpn = dash_vpn_enabled();

// One panel per category, services kept in config order.
$groups = [];
foreach ($config['categories'] as $catKey => $labels) {
    $items = array_values(array_filter($config['services'], fn($svc) => $svc['category'] === $catKey));
    if ($items) {
        $groups[] = ['key' => $catKey, 'label' => $lang === 'fr' ? $labels[0] : $labels[1], 'services' => $items];
    }
}

$refreshSeconds = 20;
$historySize = 12;
$names = [];
foreach ($config['services'] as $svc) {
    $names[$svc['key']] = $svc['name'];
}
$jsConfig = [
    'refreshSeconds' => $refreshSeconds,
    'historySize' => $historySize,
    'names' => $names,
    'strings' => $s,
];

function e(string $v): string
{
    return htmlspecialchars($v, ENT_QUOTES, 'UTF-8');
}
?>
<!DOCTYPE html>
<html lang="<?= e($lang) ?>">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light dark">
    <title>Dockarr</title>
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2318181b' stroke-width='2' stroke-linejoin='round'%3E%3Crect x='3' y='13' width='18' height='7' rx='2' fill='%23fafafa'/%3E%3Crect x='6' y='4' width='12' height='7' rx='2' fill='%23fafafa'/%3E%3C/svg%3E">
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="page">

    <header class="topbar">
        <div class="brand">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="13" width="18" height="7" rx="2"/><rect x="6" y="4" width="12" height="7" rx="2"/></svg>
            <span class="brand-name">dockarr</span>
            <span class="brand-sep"></span>
            <span class="brand-domain"><?= e($domain) ?></span>
        </div>
        <div class="controls">
            <span id="vpn-badge" class="pill<?= $vpn ? '' : ' is-alert' ?>">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6l7-3z"/></svg>
                <span class="label"><?= e($vpn ? $s['vpn_on'] : $s['vpn_off']) ?></span>
            </span>
            <span id="clock" class="clock">--:--:--</span>
            <button id="refresh" class="button" type="button">
                <svg id="refresh-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/></svg>
                <?= e($s['refresh']) ?>
            </button>
        </div>
    </header>

    <div class="progress" aria-hidden="true"><div id="progress-bar"></div></div>

    <section class="summary" aria-live="polite">
        <span class="next-check">
            <span id="live-dot" class="live-dot"></span>
            <?= e($s['next_check']) ?> <span class="num"><span id="countdown"><?= $refreshSeconds ?></span> <?= e($s['seconds']) ?></span>
        </span>
        <h1 id="headline"><?= e($s['checking']) ?></h1>
        <p id="subtitle" class="subtitle"></p>
        <p id="alert-line" class="alert-line" hidden></p>
        <div id="strip" class="strip" aria-hidden="true">
            <?php foreach ($groups as $group): ?>
                <?php foreach ($group['services'] as $svc): ?>
                    <span data-key="<?= e($svc['key']) ?>"></span>
                <?php endforeach; ?>
            <?php endforeach; ?>
        </div>
    </section>

    <main class="groups">
        <?php foreach ($groups as $group): ?>
            <section class="panel" data-group="<?= e($group['key']) ?>">
                <div class="panel-head">
                    <h2><?= e($group['label']) ?></h2>
                    <span class="panel-count">–</span>
                </div>
                <?php foreach ($group['services'] as $svc): ?>
                    <?php
                    $enabled = dash_service_enabled($svc);
                    $desc = $lang === 'fr' ? $svc['desc'][0] : $svc['desc'][1];
                    $tag = $enabled ? 'a' : 'div';
                    $attrs = $enabled
                        ? ' href="' . e("https://{$svc['subdomain']}.{$domain}") . '" target="_blank" rel="noopener noreferrer"'
                        : '';
                    ?>
                    <<?= $tag ?> class="row" data-key="<?= e($svc['key']) ?>" data-state="<?= $enabled ? 'pending' : 'disabled' ?>"<?= $attrs ?>>
                        <span class="mono"><?= e($svc['initials']) ?><span class="dot"></span></span>
                        <span class="text">
                            <span class="name"><?= e($svc['name']) ?><?php if ($enabled): ?><svg class="go" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7"/><path d="M8 7h9v9"/></svg><?php endif; ?></span>
                            <span class="desc" title="<?= e($desc) ?>"><?= e($desc) ?></span>
                        </span>
                        <span class="meta">
                            <?php if ($enabled): ?>
                                <span class="spark" aria-hidden="true"><?= str_repeat('<span></span>', $historySize) ?></span>
                            <?php endif; ?>
                            <span class="status"><?= $enabled ? '' : e($s['disabled']) ?></span>
                        </span>
                    </<?= $tag ?>>
                <?php endforeach; ?>
            </section>
        <?php endforeach; ?>
    </main>

    <footer class="footer">
        <span class="num">dashboard.<?= e($domain) ?></span>
        <span><?= e(str_replace('{n}', (string) $refreshSeconds, $s['footer'])) ?></span>
    </footer>

</div>

<script>window.DASHBOARD = <?= json_encode($jsConfig, JSON_UNESCAPED_UNICODE) ?>;</script>
<script src="assets/app.js"></script>
</body>
</html>
