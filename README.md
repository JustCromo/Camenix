# 🦎 Camenix

**Camenix** è l'app che cambia sfondo e colori del desktop Hyprland: carichi un'immagine, lei sceglie i colori a tema, tu li ritocchi guardando l'anteprima e premi *Applica*. Fa parte della suite *-nix* (Vulpnix, Racoonix, Apernix, Strinix, Erinix).

> **Stato: in sviluppo (tappa 1 di 5).** Per ora c'è il *tema centrale* (il file da cui il desktop legge i colori), il comando `camenix` e l'integrazione per Quickshell. L'app con l'anteprima arriva nella tappa 3.

## Come funziona

Tutti i colori vivono in un solo file, `~/.config/camenix/theme.json`, diviso in **ruoli** (testo, vetro, accento, secondario, successo, avviso, errore e le loro sfumature). I programmi del desktop leggono il colore del ruolo, non un colore scritto a mano: cambiando il file, cambia tutto.

Regola d'oro: **un tema rotto non rompe mai il desktop**. Valori mancanti, sbagliati o ostili vengono sostituiti da quelli predefiniti.

## Requisiti

- Hyprland
- Python 3.11 o più recente (solo libreria standard)
- Quickshell, per l'integrazione con le isole e, più avanti, per l'app

## Uso

```bash
git clone https://github.com/JustCromo/Camenix.git ~/Projects/Camenix
ln -s ~/Projects/Camenix/bin/camenix ~/.local/bin/camenix

camenix               # mostra il tema attivo (come `camenix status`)
camenix init          # crea ~/.config/camenix/theme.json con la palette predefinita
camenix check         # controlla il file del tema
camenix status --json # output stabile per script
```

Codici di uscita: `0` tutto bene, `1` problemi nel tema, `2` errore d'uso. I colori nel terminale si spengono con `NO_COLOR=1`.

## Integrazione Quickshell

Copia `integrations/quickshell/Theme.qml` nella cartella della tua shell: Quickshell lo riconosce da solo. Poi nei file QML:

```qml
color: Theme.text                 // colore del ruolo
color: Theme.a(Theme.text, 0.6)   // stesso colore con trasparenza
```

Il tema si aggiorna da solo quando il file cambia.

## Test

```bash
python3 -m unittest discover -s tests -t .
```

I test di `Theme.qml` richiedono PySide6; senza, vengono saltati.

---

# 🦎 Camenix (English)

**Camenix** changes the wallpaper and colors of your Hyprland desktop: load an image, it picks matching colors, you tweak them with a live preview and press *Apply*. Part of the *-nix* suite.

> **Status: work in progress (step 1 of 5).** Currently available: the central theme file, the `camenix` command and the Quickshell integration. The app with preview comes in step 3.

All colors live in `~/.config/camenix/theme.json`, organized in **roles**. Desktop components read role colors instead of hard-coded values. A broken or hostile theme file never breaks the desktop: invalid values fall back to the defaults.

Requirements: Hyprland, Python 3.11+ (standard library only), Quickshell for the integration. Commands: `camenix [status|init|check] [--json]`; exit codes `0` ok, `1` theme problems, `2` usage error; `NO_COLOR` supported. Tests: `python3 -m unittest discover -s tests -t .`

## Licenza / License

MIT
