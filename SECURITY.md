# Sicurezza / Security

## Cosa fa Camenix (tappa 2)

- Non usa la rete e non chiede privilegi di root.
- Scrive il tema (`~/.config/camenix/theme.json`) e le config che hai collegato (`camenix setup` o `adopt`). Prima della prima modifica ne fa una copia in `~/.config/camenix/backups` (cartella 0700).
- **Solo file sicuri**: file normali, tuoi, dentro la home. Un collegamento che porta fuori dalla home, una cartella, una FIFO o un file oltre 1 MB vengono rifiutati.
- **Tutto o niente**: prima calcola ogni file in memoria. Se uno è stato modificato a mano o un modello non si può riempire (segnaposto sconosciuto o malformato), non scrive niente e non cambia il tema.
- **Nessuna iniezione nelle config**: nei file finiscono solo colori di 6 cifre esadecimali e percorsi di sfondo assoluti senza caratteri di controllo (un "a capo" nel nome potrebbe aggiungere righe a una config).
- **Comandi esterni** (`hyprctl`, `makoctl`, `swaybg`, `swww`) sempre con argomenti fissi, mai tramite shell. I segnali (ricarica di kitty, chiusura del vecchio swaybg) vanno solo ai processi del tuo utente.
- **Sfondi**: accettati solo file con l'intestazione di un vero PNG, JPEG o WebP, fino a 64 MB.
- **Lettura difensiva**: il file non viene letto se è un collegamento simbolico o non è un file normale, e oltre i 64 KB viene ignorato. JSON rotto, colori non validi, ruoli sconosciuti e percorsi strani vengono scartati e sostituiti dai valori predefiniti.
- **Scrittura atomica**: il tema viene scritto in un file temporaneo nella stessa cartella e poi sostituito in un colpo solo, così non resta mai a metà. Il collegamento simbolico al posto del tema viene rifiutato.
- **Colori**: accettati solo nel formato `#RRGGBB`. Questo vale anche in `Theme.qml`, così nessun testo del file può diventare codice nell'interfaccia.

## Segnalare un problema

Apri una issue su GitHub **senza dettagli sfruttabili** e chiedi un contatto privato.

---

**English.** Camenix (step 2) uses no network and no root. It writes the theme and the config files you linked, after backing them up. Only regular files you own inside your home are touched; symlinks leaving home, directories, FIFOs and files over 1 MB are refused. Changes are all-or-nothing: hand-edited files or broken templates stop everything. Only 6-digit hex colors and validated absolute wallpaper paths are written into configs. External tools are called with fixed argv (no shell) and signals only reach your own processes. Wallpapers must be real PNG/JPEG/WebP files. Writes are atomic. Colors must match `#RRGGBB`, both in Python and in `Theme.qml`. To report a problem, open a GitHub issue without exploit details and ask for a private contact.
