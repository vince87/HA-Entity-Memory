# Registri persistenti

[English](PERSISTENT_REGISTERS.md) · **Italiano**

I registri persistenti permettono alle automazioni di conservare piccoli valori JSON senza creare helper visibili. Sono separati dallo storico eventi, sopravvivono ai riavvii e non compaiono nel registro entità, nelle dashboard o nel Recorder.

Sono adatti a fasi, checkpoint, flag e ultima politica applicata. Non usarli per segreti, documenti grandi, telemetria frequente o stato di sicurezza.

## Formato e limiti

- Chiavi minuscole fino a 128 caratteri: lettere, numeri, punti, trattini e underscore.
- Valori compatibili con JSON fino a 16 KiB.
- Massimo 256 registri per installazione.
- Ogni record contiene `value`, `revision` e `updated_at`.
- La revisione parte da 1 e aumenta soltanto quando cambia il valore.
- Riscrivere lo stesso valore non modifica revisione o data.

## Lettura e scrittura

```yaml
- action: entity_memory.get_register
  data:
    key: tapparelle.ovest.fase
  response_variable: registro
```

Se la chiave manca, la risposta contiene `found: false`, `value: null`, `revision: 0` e `updated_at: null`.

```yaml
- action: entity_memory.set_register
  data:
    key: tapparelle.ovest.fase
    value:
      nome: ombra
      attiva: true
  response_variable: risultato
```

La risposta indica anche `created`, `changed`, `previous` e `conflict`.

## Aggiornamenti concorrenti sicuri

Quando più esecuzioni possono scrivere la stessa chiave, passa la revisione appena letta:

```yaml
- action: entity_memory.set_register
  data:
    key: tapparelle.ovest.fase
    value: ombra
    expected_revision: "{{ registro.revision }}"
  response_variable: risultato
```

`expected_revision: 0` significa che la chiave non deve ancora esistere. Se la revisione corrente è diversa, non avviene alcuna scrittura e `conflict` vale `true`.

Sono accettati interi non negativi e stringhe composte soltanto da cifre. Booleani, valori negativi, decimali e stringhe non numeriche vengono rifiutati. L’editor YAML di Home Assistant può normalizzare `2.0` nell’intero `2`; per verificare il rifiuto di un decimale usa la stringa `'2.0'`.

## Confronto senza scrittura

```yaml
- action: entity_memory.compare_register
  data:
    key: tapparelle.ovest.fase
    value: "{{ fase_calcolata }}"
  response_variable: confronto
```

`confronto.matches` è vero soltanto se il registro esiste e il valore coincide. `compare_register` non modifica mai i dati e non accetta `expected_revision`.

## Schema periodico consigliato

1. Calcola la fase corrente.
2. Leggi il registro.
3. Considera una chiave mancante o un valore diverso come nuovo evento programmato.
4. Esegui l’azione sul dispositivo.
5. Salva la fase soltanto dopo il successo dell’azione.
6. Se la fase non è cambiata, consulta la memoria eventi prima di sovrascrivere una scelta recente.

Una variabile YAML vive soltanto durante una singola esecuzione; usa un registro quando il valore deve arrivare al trigger successivo o superare un riavvio. Per evitare sovrapposizioni usa `mode: single` oppure `expected_revision`.

## Elenco ed eliminazione

```yaml
- action: entity_memory.list_registers
  data:
    prefix: tapparelle.
    limit: 100
  response_variable: registri
```

```yaml
- action: entity_memory.delete_register
  data:
    key: tapparelle.ovest.fase
  response_variable: eliminazione
```

Rimuovere e riaggiungere l’integrazione non azzera i registri. Quando ritiri un’automazione, elimina esplicitamente le chiavi del suo namespace.

## Affidabilità e privacy

Una versione futura e non supportata del formato di archiviazione viene rifiutata senza sovrascrivere i dati. Una scrittura già entrata nella fase di salvataggio viene completata prima di propagare l’annullamento.

La diagnostica contiene soltanto conteggi, dimensioni codificate, limiti e versione del formato. Non include chiavi, valori o ID delle entità osservate.
