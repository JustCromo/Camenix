# Sicurezza / Security

## Cosa fa Camenix (tappa 1)

- Legge e scrive un solo file: `~/.config/camenix/theme.json`. Non usa la rete, non chiede privilegi di root e non esegue comandi.
- **Lettura difensiva**: il file non viene letto se è un collegamento simbolico o non è un file normale, e oltre i 64 KB viene ignorato. JSON rotto, colori non validi, ruoli sconosciuti e percorsi strani vengono scartati e sostituiti dai valori predefiniti.
- **Scrittura atomica**: il tema viene scritto in un file temporaneo nella stessa cartella e poi sostituito in un colpo solo, così non resta mai a metà. Il collegamento simbolico al posto del tema viene rifiutato.
- **Colori**: accettati solo nel formato `#RRGGBB`. Questo vale anche in `Theme.qml`, così nessun testo del file può diventare codice nell'interfaccia.

## Segnalare un problema

Apri una issue su GitHub **senza dettagli sfruttabili** e chiedi un contatto privato.

---

**English.** Camenix (step 1) reads and writes only `~/.config/camenix/theme.json`, with no network, no root and no command execution. Symlinks and non-regular files are refused, files over 64 KB are ignored, and invalid values fall back to defaults. Writes are atomic. Colors must match `#RRGGBB`, both in Python and in `Theme.qml`. To report a problem, open a GitHub issue without exploit details and ask for a private contact.
