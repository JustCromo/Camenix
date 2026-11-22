# 🦎 Camenix

**Camenix** è l'app che cambia sfondo e colori del desktop Hyprland: carichi un'immagine, lei sceglie i colori a tema, tu li ritocchi guardando l'anteprima e premi *Applica*. Fa parte della suite *-nix* (Vulpnix, Racoonix, Apernix, Strinix, Erinix).

> **Stato: in sviluppo (tappa 2 di 5).** Funzionano il *tema centrale*, il comando `camenix` e il collegamento del tema a sfondo, Hyprland, kitty, rofi, mako, hyprlock e Quickshell. L'app con l'anteprima arriva nella tappa 3.

## Come funziona

Tutti i colori vivono in un solo file, `~/.config/camenix/theme.json`, diviso in **ruoli** (testo, vetro, accento, secondario, successo, avviso, errore e le loro sfumature). I programmi del desktop leggono il colore del ruolo, non un colore scritto a mano: cambiando il file, cambia tutto.

Regola d'oro: **un tema rotto non rompe mai il desktop**. Valori mancanti, sbagliati o ostili vengono sostituiti da quelli predefiniti.

### Come raggiunge i programmi

| Programma | Come | Ricarica |
|---|---|---|
| kitty | una riga `include` verso i colori generati | subito (`SIGUSR1`) |
| rofi, mako, hyprlock, bordi di Hyprland | **modello**: i colori del file diventano segnaposto (`#{{cmx:accent}}`) e Camenix riscrive il file a ogni *Applica* | mako e Hyprland subito; rofi e hyprlock alla prossima apertura |
| sfondo | `camenix wallpaper` con swww, hyprpaper o swaybg | subito |
| Quickshell | `Theme.qml` legge il tema da solo | subito |

**Regole di sicurezza dei file**: copia di sicurezza prima della prima modifica (`~/.config/camenix/backups`); **tutto o niente** (se un file è stato modificato a mano o un modello non torna, non viene scritto niente e il tema non cambia); solo file normali tuoi dentro la home (i collegamenti stile GNU Stow vanno bene, quelli che escono dalla home no).

Se modifichi a mano un file collegato, `camenix apply` si ferma e te lo dice: con `camenix adopt <file>` Camenix tiene le tue modifiche; con `camenix forget <file>` smette di gestirlo.

## Requisiti

- Hyprland
- Python 3.11 o più recente (solo libreria standard)
- Quickshell, per l'integrazione con le isole e, più avanti, per l'app

## Uso

```bash
git clone https://github.com/JustCromo/Camenix.git ~/Projects/Camenix
ln -s ~/Projects/Camenix/bin/camenix ~/.local/bin/camenix

camenix                       # mostra il tema attivo e i file collegati (come `camenix status`)
camenix setup --dry-run       # mostra cosa farebbe la prima configurazione, senza toccare niente
camenix setup                 # crea il tema, salva lo sfondo attuale, collega le config
camenix apply                 # applica il tema a tutto il desktop
camenix set accent "#3FE0D0"  # cambia un colore e applica
camenix wallpaper set ~/img.png   # cambia sfondo e applica
camenix wallpaper             # mostra lo sfondo del tema (da usare all'avvio)
camenix undo                  # torna al tema precedente (ultimi 20)
camenix adopt <file>          # collega un file (o riprende le tue modifiche a mano)
camenix forget <file>         # smette di gestire un file
camenix check                 # controlla il file del tema
```

Codici di uscita: `0` tutto bene, `1` problemi nel tema, `2` errore d'uso. I colori nel terminale si spengono con `NO_COLOR=1`.

## Integrazione Quickshell

Copia `integrations/quickshell/Theme.qml` nella cartella della tua shell: Quickshell lo riconosce da solo. Poi nei file QML:

```qml
color: Theme.text                 // colore del ruolo
color: Theme.a(Theme.text, 0.6)   // stesso colore con trasparenza
```

Il tema si aggiorna da solo quando il file cambia. Se `Theme.qml` è in `~/.config/quickshell/`, `camenix apply` lo tiene aggiornato.

Per lo sfondo all'avvio, al posto del comando di swaybg/swww/hyprpaper nella config di Hyprland usa:

```
camenix wallpaper
```

## Test

```bash
python3 -m unittest discover -s tests -t .
```

I test di `Theme.qml` richiedono PySide6; senza, vengono saltati.

---

# 🦎 Camenix (English)

**Camenix** changes the wallpaper and colors of your Hyprland desktop: load an image, it picks matching colors, you tweak them with a live preview and press *Apply*. Part of the *-nix* suite.

> **Status: work in progress (step 2 of 5).** Currently available: the central theme file, the `camenix` command, and theming of wallpaper, Hyprland borders, kitty, rofi, mako, hyprlock and Quickshell. The app with preview comes in step 3.

All colors live in `~/.config/camenix/theme.json`, organized in **roles**. Desktop components read role colors instead of hard-coded values. A broken or hostile theme file never breaks the desktop: invalid values fall back to the defaults.

kitty gets an `include` line; rofi, mako, hyprlock and Hyprland borders are handled through **templates** (colors become `#{{cmx:role}}` placeholders and the file is rewritten on apply). Every change is all-or-nothing, with backups first; hand-edited files block the apply until you run `camenix adopt <file>`. Wallpaper via swww, hyprpaper or swaybg (`camenix wallpaper` at startup).

Requirements: Hyprland, Python 3.11+ (standard library only), Quickshell for the integration. Commands: `camenix [status|init|check|setup|apply|set|wallpaper|undo|adopt|forget] [--json]`; exit codes `0` ok, `1` theme problems, `2` usage error; `NO_COLOR` supported. Tests: `python3 -m unittest discover -s tests -t .`

## Licenza / License

MIT
