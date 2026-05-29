import sys

from . import secrets as secretsmod


def _t(lang, en, fr):
    """Pick the English or French string for the chosen language."""
    return fr if lang == "fr" else en


def _ask_yes_no(prompt, default_yes):
    """Prompt for a yes/no answer, accepting o/y/n in either language."""
    default = "y" if default_yes else "n"
    choice = None
    while choice not in ("o", "n", "y"):
        choice = input(prompt).strip().lower() or default
    return choice in ("o", "y")


def ensure_language(store):
    """Ask once which language to use. This runs first, so every later prompt is
    shown in the chosen language. 'en' (default) changes nothing; 'fr' configures
    Jellyfin and Seerr in French."""
    if store.language:
        return

    if not sys.stdin.isatty():
        store.set_language("en")
        print("[bootstrap] non-interactive run: language=en")
        return

    print("\nLanguage / Langue:")
    print("  [1] English (default)")
    print("  [2] Français")
    choice = ""
    while choice not in ("1", "2"):
        choice = input("Choice / Choix [1/2] : ").strip() or "1"
    store.set_language("fr" if choice == "2" else "en")
    print(f"  -> {'Français' if choice == '2' else 'English'}\n")


def ensure_policy(store):
    """Establish the credential policy once. Interactive on first run;
    falls back to safe defaults when no TTY is attached (automation)."""
    if store.policy:
        return

    if not sys.stdin.isatty():
        username = secretsmod.gen_username()
        store.set_policy(username, "per_service")
        print(f"[bootstrap] non-interactive run: username='{username}', "
              "random password per service")
        return

    lang = store.language or "en"
    print(_t(lang, "\n=== Dockarr bootstrap: first run ===",
                   "\n=== Dockarr bootstrap : premier lancement ==="))
    raw = input(_t(lang,
                   "Service username? [empty = random a-z(10)] : ",
                   "Identifiant de service ? [vide = aléatoire a-z(10)] : ")).strip()
    username = raw or secretsmod.gen_username()
    print(_t(lang, f"  -> username: {username}", f"  -> identifiant : {username}"))

    print(_t(lang, "Password mode:", "Mode de mot de passe :"))
    print(_t(lang, "  [1] same random password everywhere",
                   "  [1] même mot de passe aléatoire partout"))
    print(_t(lang, "  [2] a different random password per service",
                   "  [2] un mot de passe aléatoire différent par service"))
    choice = ""
    while choice not in ("1", "2"):
        choice = input(_t(lang, "Choice [1/2] : ", "Choix [1/2] : ")).strip()

    if choice == "1":
        store.set_policy(username, "shared", secretsmod.gen_password())
        print(_t(lang, "  -> shared random password generated",
                       "  -> mot de passe aléatoire partagé généré"))
    else:
        store.set_policy(username, "per_service")
        print(_t(lang, "  -> a random password will be generated per service",
                       "  -> un mot de passe aléatoire sera généré par service"))

    print(_t(lang, f"Credentials are stored in {store.path}\n",
                   f"Identifiants stockés dans {store.path}\n"))


def ensure_kavita(store):
    """Ask once whether to run Kavita. If declined, the kavita module stops the
    container (started by `make up`) and skips its provisioning."""
    if store.kavita is not None:
        return

    if not sys.stdin.isatty():
        store.set_kavita(True)
        print("[bootstrap] non-interactive run: Kavita enabled")
        return

    lang = store.language or "en"
    print(_t(lang, "\nKavita, book / comic / manga server:",
                   "\nKavita, serveur de livres / BD / mangas :"))
    enabled = _ask_yes_no(
        _t(lang, "Enable Kavita? [Y/n] : ", "Activer Kavita ? [O/n] : "),
        default_yes=True,
    )
    store.set_kavita(enabled)
    if enabled:
        print(_t(lang, "  -> Kavita enabled\n", "  -> Kavita activé\n"))
    else:
        print(_t(lang, "  -> Kavita disabled (container stopped)\n",
                       "  -> Kavita désactivé (conteneur arrêté)\n"))


# (env var, English label, French label, default). gluetun reads these from .env.
VPN_FIELDS = [
    ("VPN_SERVICE_PROVIDER", "VPN provider (e.g. mullvad, protonvpn)",
     "Fournisseur VPN (ex. mullvad, protonvpn)", None),
    ("VPN_TYPE", "VPN type", "Type de VPN", "wireguard"),
    ("WIREGUARD_PRIVATE_KEY", "WireGuard private key", "Clé privée WireGuard", None),
    ("WIREGUARD_ADDRESSES", "WireGuard addresses (e.g. 10.2.0.2/32)",
     "Adresses WireGuard (ex. 10.2.0.2/32)", None),
    ("SERVER_COUNTRIES", "Exit countries (e.g. Switzerland)",
     "Pays de sortie (ex. Switzerland)", None),
]


def ensure_vpn(store):
    """Ask once whether to route qBittorrent through Gluetun (VPN). If enabled,
    collect the WireGuard credentials; the vpn module mirrors them into .env and
    flips COMPOSE_FILE to the VPN overlay. Disabled by default and without a TTY,
    since the VPN can't run without real credentials."""
    if store.vpn is not None:
        return

    if not sys.stdin.isatty():
        store.set_vpn(False)
        print("[bootstrap] non-interactive run: VPN disabled")
        return

    lang = store.language or "en"
    print(_t(lang, "\nVPN (Gluetun): route qBittorrent through a WireGuard VPN:",
                   "\nVPN (Gluetun) : router qBittorrent à travers un VPN WireGuard :"))
    print(_t(lang, "  Requires a VPN subscription (WireGuard private key, etc.).",
                   "  Nécessite un abonnement VPN (clé privée WireGuard, etc.)."))
    if not _ask_yes_no(
        _t(lang, "Enable the VPN? [y/N] : ", "Activer le VPN ? [o/N] : "),
        default_yes=False,
    ):
        store.set_vpn(False)
        print(_t(lang, "  -> VPN disabled\n", "  -> VPN désactivé\n"))
        return

    creds = {}
    for key, label_en, label_fr, default in VPN_FIELDS:
        label = _t(lang, label_en, label_fr)
        suffix = f" [{default}]" if default else ""
        creds[key] = input(f"  {label}{suffix} : ").strip() or (default or "")
    store.set_vpn(True, **creds)
    print(_t(lang, "  -> VPN enabled (credentials saved; adjustable in .env)\n",
                   "  -> VPN activé (identifiants enregistrés ; ajustables dans .env)\n"))


DEFAULT_FR_PROFILE = "1080p Efficient FR"


def ensure_profilarr_fr(store):
    """Ask once whether to auto-configure Profilarr with the French regex
    database. If enabled, the profilarr-fr module wipes Profilarr's database,
    clones the French DB and pushes the chosen profile to Radarr/Sonarr."""
    if store.profilarr_fr is not None:
        return

    if not sys.stdin.isatty():
        store.set_profilarr_fr(False)
        print("[bootstrap] non-interactive run: Profilarr FR auto-config disabled")
        return

    lang = store.language or "en"
    print(_t(lang, "\nProfilarr: French auto-configuration:",
                   "\nProfilarr : auto-configuration française :"))
    print(_t(lang, "  Replaces the Profilarr database with the French one (custom",
                   "  Remplace la base Profilarr par la base FR (custom formats +"))
    print(_t(lang, "  formats + profiles tuned for French content), then applies it",
                   "  profils optimisés pour le contenu francophone) puis l'applique"))
    print(_t(lang, "  to Radarr/Sonarr.", "  à Radarr/Sonarr."))
    print(_t(lang, "  WARNING: deletes the existing Profilarr database.",
                   "  ATTENTION : supprime la base de données Profilarr existante."))
    if not _ask_yes_no(
        _t(lang, "Enable FR auto-config? [y/N] : ", "Activer l'auto-config FR ? [o/N] : "),
        default_yes=False,
    ):
        store.set_profilarr_fr(False)
        print(_t(lang, "  -> FR auto-config disabled\n", "  -> auto-config FR désactivée\n"))
        return

    profile = input(_t(lang, f"Default profile [{DEFAULT_FR_PROFILE}] : ",
                             f"Profil par défaut [{DEFAULT_FR_PROFILE}] : ")).strip() \
        or DEFAULT_FR_PROFILE
    store.set_profilarr_fr(True, profile)
    print(_t(lang, f"  -> FR auto-config enabled (profile: {profile})\n",
                   f"  -> auto-config FR activée (profil : {profile})\n"))
