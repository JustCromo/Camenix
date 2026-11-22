# 🦎 Camenix

**Camenix** è l'app che cambia **sfondo e colori** del desktop Hyprland. Carichi un'immagine, ritocchi i colori guardando l'anteprima di home e schermata di blocco, e premi **Applica**. Fa parte della suite *-nix* (Vulpnix, Racoonix, Apernix, Strinix, Erinix).

> **Stato: in sviluppo (tappa 4 di 5).** L'app c'è: anteprima, colori per zona con selettore (ruota, R G B, colori dello sfondo), sfondo, *Applica* con paracadute, tema chiaro/scuro. In arrivo: palette proposta in automatico dallo sfondo (fine tappa 4), tema GTK (tappa 5).

## Come si usa

Apri **Camenix** dal menu delle applicazioni (o con il comando `camenix`).

- **Anteprima**: a sinistra vedi il desktop (isole, terminale, menu) e la schermata di blocco con i colori che stai scegliendo. Il desktop vero non cambia finché non premi *Applica*.
- **Carica sfondo…**: scegli un PNG, JPEG o WebP. Camenix ne tiene una copia, quindi il tema non si rompe se sposti l'originale. Con l'interruttore decidi se il blocco usa lo stesso sfondo (sfocato) o uno diverso.
- **Colori, per zona**: *Isole e menu*, *Bordi delle finestre* (inizio e fine del gradiente), *Terminale*, *Avvisi*. Passando il mouse su un colore, nell'anteprima si illumina dove compare. Le **sfumature** (hover, varianti chiare e scure) seguono da sole; i due colori dei bordi li scegli tu. Su *Testo* c'è il controllo di leggibilità.
- **Selettore**: anello delle tinte con il quadrato saturazione/luminosità, cursori **R G B**, campo `#hex`, i colori principali del tuo sfondo e quelli del tema, *prima/dopo*. Invio conferma solo un `#hex` completo.
- **Applica ✓**: il tema va su tutto il desktop e compare *"Tenere il nuovo tema?"*. Se non premi **Tieni** entro 15 secondi, torna quello di prima: utile se un colore rende lo schermo illeggibile.
- **Colori originali**: torna alla palette di partenza tenendo lo sfondo.
- **☀ / ☾**: tema chiaro o scuro dell'app (ricordato).

Se un file di config è stato modificato a mano, Camenix **non applica niente** e te lo mostra: con *Tieni le mie modifiche* il file viene ricollegato con le tue modifiche e si riprova.

## Cosa cambia sul desktop

| Programma | Come | Quando si vede |
|---|---|---|
| Quickshell (isole) | `Theme.qml` legge il tema da solo | subito |
| kitty | una riga `include` verso i colori generati | subito |
| rofi, mako, hyprlock, bordi di Hyprland | **modello**: i colori del file diventano segnaposto (`#{{cmx:accent}}`) e Camenix riscrive il file | mako e Hyprland subito, rofi e hyprlock alla prossima apertura |
| sfondo | swww, hyprpaper o swaybg | subito |

**Sicurezza dei file**: copia di sicurezza prima della prima modifica (`~/.config/camenix/backups`), **tutto o niente** (se qualcosa non torna non viene scritto nulla e il tema non cambia), e solo file normali tuoi dentro la home. Dettagli in [SECURITY.md](SECURITY.md).

## Installazione

Requisiti: Hyprland, Quickshell (`qs`), Python 3.11+ (solo libreria standard), zenity o kdialog per scegliere i file.

```bash
git clone https://github.com/JustCromo/Camenix.git ~/Projects/Camenix
ln -s ~/Projects/Camenix/bin/camenix ~/.local/bin/camenix
~/Projects/Camenix/bin/camenix-engine setup     # collega le config che trova (prima: setup --dry-run)
~/Projects/Camenix/bin/camenix-engine install   # voce "Camenix" nel menu delle applicazioni
```

Per lo sfondo all'avvio, nella config di Hyprland sostituisci il comando di swaybg/swww/hyprpaper con:

```
~/Projects/Camenix/bin/camenix-engine wallpaper
```

Per far aprire la finestra flottante e centrata, aggiungi una regola di Hyprland per il titolo `Camenix`.

Per le isole Quickshell: copia `integrations/quickshell/Theme.qml` nella cartella della shell e usa `Theme.text`, `Theme.accent`, `Theme.a(Theme.text, 0.6)`… al posto dei colori scritti a mano.

## Per sviluppatori

L'app (`app/`, QML per Quickshell) non scrive mai le config da sola: passa sempre dal **motore** `bin/camenix-engine` (Python), che valida tutto e risponde in JSON (`status`, `apply-file`, `derive`, `import-wallpaper`, `reset-colors`, `undo`, `setup`, `adopt`, `forget`, `wallpaper`, `install`; codici di uscita `0` ok, `1` problema, `2` uso errato).

```bash
python3 -m unittest discover -s tests -t .
```

I test dell'interfaccia (QML) richiedono PySide6; senza, vengono saltati.

---

# 🦎 Camenix (English)

**Camenix** is a desktop app that changes the **wallpaper and colors** of a Hyprland desktop. Load an image, tweak colors with a live preview of desktop and lock screen, press **Apply**. A 15-second safety prompt reverts automatically unless you press **Keep**. Light/dark app theme, shades that follow the main colors, readability check.

It themes Quickshell (live `Theme.qml`), kitty (`include`), rofi/mako/hyprlock/Hyprland borders (templates with `#{{cmx:role}}` placeholders) and the wallpaper (swww, hyprpaper or swaybg). Changes are all-or-nothing, with backups first; hand-edited files are never overwritten.

Requirements: Hyprland, Quickshell, Python 3.11+ (stdlib only), zenity or kdialog. Setup: `bin/camenix-engine setup`, `bin/camenix-engine install`, then open **Camenix** from your launcher. Tests: `python3 -m unittest discover -s tests -t .` (QML tests need PySide6).

## Licenza / License

MIT
