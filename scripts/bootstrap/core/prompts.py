import sys

from . import secrets as secretsmod


def ensure_language(store):
    """Ask once whether to localize the stack. 'en' (default) changes nothing;
    'fr' configures Jellyfin and Seerr in French."""
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


def ensure_kavita(store):
    """Ask once whether to run Kavita. If declined, the kavita module stops the
    container (started by `make up`) and skips its provisioning."""
    if store.kavita is not None:
        return

    if not sys.stdin.isatty():
        store.set_kavita(True)
        print("[bootstrap] non-interactive run: Kavita enabled")
        return

    print("\nKavita — serveur de livres / BD / mangas:")
    choice = None
    while choice not in ("o", "n", "y"):
        choice = input("Activer Kavita ? [O/n] : ").strip().lower() or "o"

    enabled = choice in ("o", "y")
    store.set_kavita(enabled)
    print(f"  -> Kavita {'activé' if enabled else 'désactivé (conteneur arrêté)'}\n")


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

    print("\nProfilarr — auto-configuration française:")
    print("  Remplace la base Profilarr par la base FR (custom formats + profils")
    print("  optimisés pour le contenu francophone) puis l'applique à Radarr/Sonarr.")
    print("  ATTENTION: supprime la base de données Profilarr existante.")
    choice = None
    while choice not in ("o", "n", "y"):
        choice = input("Activer l'auto-config FR ? [o/N] : ").strip().lower() or "n"

    if choice in ("o", "y"):
        profile = (
            input(f"Profil par défaut [{DEFAULT_FR_PROFILE}] : ").strip()
            or DEFAULT_FR_PROFILE
        )
        store.set_profilarr_fr(True, profile)
        print(f"  -> auto-config FR activée (profil : {profile})\n")
    else:
        store.set_profilarr_fr(False)
        print("  -> auto-config FR désactivée\n")


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

    print("\n=== Dockarr bootstrap — first run ===")
    raw = input("Service username? [empty = random a-z(10)] : ").strip()
    username = raw or secretsmod.gen_username()
    print(f"  -> username: {username}")

    print("Password mode:")
    print("  [1] same random password everywhere")
    print("  [2] a different random password per service")
    choice = ""
    while choice not in ("1", "2"):
        choice = input("Choice [1/2] : ").strip()

    if choice == "1":
        store.set_policy(username, "shared", secretsmod.gen_password())
        print("  -> shared random password generated")
    else:
        store.set_policy(username, "per_service")
        print("  -> a random password will be generated per service")

    print(f"Credentials are stored in {store.path}\n")
