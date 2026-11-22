# Sicurezza / Security

## Cosa fa Camenix (tappa 4)

- Non usa la rete e non chiede privilegi di root.
- Scrive il tema (`~/.config/camenix/theme.json`) e le config che hai collegato (`camenix setup` o `adopt`). Prima della prima modifica ne fa una copia in `~/.config/camenix/backups` (cartella 0700).
- **Solo file sicuri**: file normali, tuoi, dentro la home. Un collegamento che porta fuori dalla home, una cartella, una FIFO o un file oltre 1 MB vengono rifiutati.
- **Tutto o niente**: prima calcola ogni file in memoria. Se uno è stato modificato a mano o un modello non si può riempire (segnaposto sconosciuto o malformato), non scrive niente e non cambia il tema.
- **Nessuna iniezione nelle config**: nei file finiscono solo colori di 6 cifre esadecimali e percorsi di sfondo assoluti senza caratteri di controllo (un "a capo" nel nome potrebbe aggiungere righe a una config).
- **Comandi esterni** (`hyprctl`, `makoctl`, `swaybg`, `swww`) sempre con argomenti fissi, mai tramite shell. I segnali (ricarica di kitty, chiusura del vecchio swaybg) vanno solo ai processi del tuo utente.
- **Sfondi**: accettati solo file con l'intestazione di un vero PNG, JPEG o WebP, fino a 64 MB. L'immagine scelta viene copiata in `~/.config/camenix/wallpapers` (0700).
- **L'app non scrive le config**: salva solo le sue preferenze (`app.json`). La bozza passa al motore come argomento (mai tramite shell), e il motore la tratta come input non fidato, con le stesse regole del tema.
- **Primo avvio**: la lettura dei colori del desktop (`detect`) non scrive niente e usa le stesse regole dei file sicuri (solo file tuoi dentro la home, al massimo 1 MB, `include` di kitty seguiti per due livelli e mai fuori dalla home). Le config vengono collegate solo dopo «Inizia», con copia di sicurezza; se un tema esiste già il primo avvio si rifiuta di sovrascriverlo. I «colori iniziali» (`original.json`) vengono riletti con gli stessi controlli del tema.
- **Selettore**: i colori dello sfondo vengono letti dall'app rimpicciolendo l'immagine già scelta; nessun file nuovo, nessuna rete.
- **Paracadute**: dopo *Applica*, se non confermi entro 15 secondi il tema precedente viene ripristinato dallo storico.
- **Voce di menu**: il file `.desktop` contiene solo percorsi assoluti; percorsi con caratteri speciali (spazi, `;`, `$`, apici…) vengono rifiutati.
- **Lettura difensiva**: il file non viene letto se è un collegamento simbolico o non è un file normale, e oltre i 64 KB viene ignorato. JSON rotto, colori non validi, ruoli sconosciuti e percorsi strani vengono scartati e sostituiti dai valori predefiniti.
- **Scrittura atomica**: il tema viene scritto in un file temporaneo nella stessa cartella e poi sostituito in un colpo solo, così non resta mai a metà. Il collegamento simbolico al posto del tema viene rifiutato.
- **Colori**: accettati solo nel formato `#RRGGBB`. Questo vale anche in `Theme.qml`, così nessun testo del file può diventare codice nell'interfaccia.

## Segnalare un problema

Apri una issue su GitHub **senza dettagli sfruttabili** e chiedi un contatto privato.

---

**English.** Camenix (step 4) uses no network and no root. It writes the theme and the config files you linked, after backing them up. Only regular files you own inside your home are touched; symlinks leaving home, directories, FIFOs and files over 1 MB are refused. Changes are all-or-nothing: hand-edited files or broken templates stop everything. Only 6-digit hex colors and validated absolute wallpaper paths are written into configs. External tools are called with fixed argv (no shell) and signals only reach your own processes. Wallpapers must be real PNG/JPEG/WebP files and are copied into a private folder. The app itself only writes its preferences; the draft is passed to the engine as an argument (no shell) and validated like any untrusted input. First run only reads your configs (same safe-file rules, kitty includes followed at most two levels and never outside home) and links them only after you press Start, with backups; it never overwrites an existing theme. After Apply, the previous theme is restored unless you confirm within 15 seconds. Writes are atomic. Colors must match `#RRGGBB`, both in Python and in `Theme.qml`. To report a problem, open a GitHub issue without exploit details and ask for a private contact.
