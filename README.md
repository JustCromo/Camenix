# 🦎 Camenix

**Camenix** è l'app che cambia **sfondo e colori** del desktop Hyprland, in tre passi: **① Sfondo**, **② Colori**, **③ Applica**, con l'anteprima di scrivania e schermata di blocco sempre a sinistra. Fa parte della suite *-nix* (Vulpnix, Racoonix, Apernix, Strinix, Erinix).

> **Stato: in sviluppo (tappa 4 di 5).** Ci sono: primo avvio che legge i colori del desktop, tre passi, colori per zona con selettore (anello delle tinte, R G B, colori dello sfondo), *Applica* con paracadute, tema chiaro/scuro. In arrivo: palette proposta in automatico dallo sfondo (fine tappa 4), tema GTK (tappa 5).

## Come si usa

Apri **Camenix** dal menu delle applicazioni (o con il comando `camenix`).

- **Primo avvio**: Camenix guarda il desktop e ti mostra i colori che usi già (bordi di Hyprland, kitty, notifiche di mako, sfondo) e cosa collegherà. Finché non premi **Inizia** non tocca niente. Quei colori diventano il punto di partenza e i *colori iniziali* a cui puoi sempre tornare: Camenix non impone un suo tema.
- **① Sfondo**: scegli un PNG, JPEG o WebP per la scrivania (Camenix ne tiene una copia, quindi puoi spostare l'originale). Per il blocco schermo: lo stesso sfondo sfocato, oppure un'altra immagine.
- **② Colori**, divisi per zona: *Isole e menu*, *Bordi delle finestre* (inizio e fine del gradiente), *Terminale*, *Avvisi*. Passando il mouse su un colore, nell'anteprima si illumina dove compare. Le **sfumature** seguono da sole; i due colori dei bordi li scegli tu. *Torna ai colori iniziali* rimette quelli di partenza, tenendo lo sfondo.
- **Selettore**: anello delle tinte con il quadrato saturazione/luminosità, cursori **R G B**, campo `#hex`, i colori principali del tuo sfondo e quelli del tema, *prima/dopo*, e per testo e sfondo il controllo di leggibilità. Invio conferma solo un `#hex` completo.
- **③ Applica**: l'elenco di cosa cambia (prima → dopo) e dove arriva. Dopo *Applica* compare *"Tenere il nuovo tema?"*: se non premi **Tieni** entro 15 secondi torna tutto com'era.
- **☀ / ☾**: tema chiaro o scuro dell'app (ricordato). L'app ha colori suoi, non quelli del desktop, così resta leggibile qualunque tema tu scelga.

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
~/Projects/Camenix/bin/camenix-engine install   # voce "Camenix" nel menu delle applicazioni
```

Poi apri Camenix: al primo avvio legge i colori del desktop e, quando premi **Inizia**, collega le config da solo.

Per lo sfondo all'avvio, nella config di Hyprland sostituisci il comando di swaybg/swww/hyprpaper con:

```
~/Projects/Camenix/bin/camenix-engine wallpaper
```

Per far aprire la finestra flottante e centrata, aggiungi una regola di Hyprland per il titolo `Camenix`.

Per le isole Quickshell: copia `integrations/quickshell/Theme.qml` nella cartella della shell e usa `Theme.text`, `Theme.accent`, `Theme.a(Theme.text, 0.6)`… al posto dei colori scritti a mano.

## Per sviluppatori

L'app (`app/`, QML per Quickshell) non scrive mai le config da sola: passa sempre dal **motore** `bin/camenix-engine` (Python), che valida tutto e risponde in JSON (`status`, `detect`, `first-run`, `apply-draft`, `derive`, `import-wallpaper`, `reset-colors`, `undo`, `setup`, `adopt`, `forget`, `wallpaper`, `install`; codici di uscita `0` ok, `1` problema, `2` uso errato).

```bash
python3 -m unittest discover -s tests -t .
```

I test dell'interfaccia (QML) richiedono PySide6; senza, vengono saltati.

---

# 🦎 Camenix (English)

**Camenix** is a desktop app that changes the **wallpaper and colors** of a Hyprland desktop in three steps (**Wallpaper → Colors → Apply**) with a live preview of desktop and lock screen. On first run it reads the colors your desktop already uses (Hyprland borders, kitty, mako, wallpaper) and starts from those, touching nothing until you press **Start**. Colors are grouped by area, hovering one highlights where it appears, and the picker has a hue ring, RGB sliders, hex input and colors taken from your wallpaper. A 15-second safety prompt reverts automatically unless you press **Keep**.

It themes Quickshell (live `Theme.qml`), kitty (`include`), rofi/mako/hyprlock/Hyprland borders (templates with `#{{cmx:role}}` placeholders) and the wallpaper (swww, hyprpaper or swaybg). Changes are all-or-nothing, with backups first; hand-edited files are never overwritten.

Requirements: Hyprland, Quickshell, Python 3.11+ (stdlib only), zenity or kdialog. Setup: `bin/camenix-engine install`, then open **Camenix** from your launcher; first run links your configs when you press **Start**. Tests: `python3 -m unittest discover -s tests -t .` (QML tests need PySide6).

## Licenza / License

MIT
