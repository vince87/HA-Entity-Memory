# Guida Entity Memory per assistenti IA

[English](AI_AUTOMATION_GUIDE.md) · **Italiano**

Questo documento è il contratto operativo per gli assistenti IA che generano automazioni Home Assistant con Entity Memory `0.2.0`. Non attribuire mai un’origine con certezza maggiore di quella restituita dall’integrazione.

## Ordine obbligatorio di progettazione

Genera la logica in questo ordine:

1. **Vincoli assoluti di sicurezza:** antifurto, serrature, incendio, pioggia, vento, gelo o altri interblocchi dichiarati dall’utente.
2. **Eventi programmati:** confine orario o cambiamento di una fase calcolata.
3. **Scelte umane o incerte ricordate:** conservarle fino al successivo evento programmato quando questa è la regola richiesta.
4. **Comportamenti di comodità:** polling, tentativi, notifiche e regolazioni accessorie.

Entity Memory aiuta nei punti 2 e 3, ma non deve mai indebolire il punto 1. Se l’antifurto è un vincolo assoluto, controllalo prima della soppressione dovuta a un override manuale e applica comunque l’azione richiesta.

Prima di scrivere YAML, ottieni o dichiara chiaramente le ipotesi su:

- ID delle entità e azione prevista;
- vincoli assoluti e stati attivi, compresi stati transitori come `arming`;
- orari e regole delle fasi calcolate;
- durata dell’autorità di una scelta ricordata;
- comportamento iniziale quando storico o registro mancano;
- modalità dell’automazione e gestione delle esecuzioni sovrapposte.

## Ambito

Entity Memory conserva cambiamenti significativi per `light`, `cover`, `climate`, `switch` e `binary_sensor`. Ripristina una finestra limitata dal Recorder e segue i nuovi cambiamenti dal vivo. È un aiuto decisionale, non un sistema di sicurezza.

Sostituisci sempre ID, soglie, durate, modalità e setpoint di esempio con valori forniti o approvati dall’utente. Non pubblicare ID reali di entità, utenti o contesti, né token.

## Azioni della memoria eventi

Tutte le azioni restituiscono dati e normalmente richiedono `response_variable`.

### `entity_memory.get_events`

Restituisce gli eventi dal più recente al più vecchio.

```yaml
- action: entity_memory.get_events
  data:
    entity_id:
      - climate.climatizzatore_esempio
    since: "02:00:00"
    origins:
      - authenticated_command
      - external_or_physical
    limit: 20
  response_variable: memoria
```

`memoria.events` è una lista e `memoria.count` ne indica la lunghezza.

### `entity_memory.last_event`

Restituisce il più recente evento corrispondente. `memoria.event` è un oggetto oppure `none`; `memoria.found` è booleano.

### `entity_memory.was_changed`

Indica se esiste almeno un evento corrispondente.

```yaml
- action: entity_memory.was_changed
  data:
    entity_id:
      - climate.climatizzatore_esempio
    since: "02:00:00"
    to_state: "off"
    origins:
      - authenticated_command
      - external_or_physical
  response_variable: memoria
```

### `entity_memory.count_events`

Conta gli eventi corrispondenti; `memoria.count` è un intero.

I filtri possono comprendere entità, intervallo temporale, stato precedente, nuovo stato e origine. Usa la finestra più breve che soddisfa lo scopo.

## Registri persistenti

I registri sono valori nominati e privi di entità per ricordare fasi, checkpoint, flag o l’ultima politica applicata. Sopravvivono ai riavvii, non compaiono nelle dashboard e sono separati dal Recorder.

Azioni disponibili:

- `get_register`: legge una chiave;
- `set_register`: crea o sostituisce un valore;
- `compare_register`: confronta senza scrivere;
- `delete_register`: elimina una chiave;
- `list_registers`: elenca le chiavi, anche per prefisso.

Preferisci chiavi leggibili come `tapparelle.ovest.piano_1`; non comprimere significati indipendenti in una maschera di bit non documentata. Non usare registri per segreti, stato di sicurezza, documenti grandi o telemetria frequente.

Le variabili di un’automazione esistono soltanto durante quella esecuzione. Usa un registro se il valore deve arrivare al trigger successivo o superare un ricaricamento o riavvio.

## Fase calcolata ed evento programmato

Un’unica automazione periodica può trasformare una soglia variabile, per esempio solare, in un evento programmato:

1. calcola la fase corrente;
2. legge il registro della fase;
3. considera una chiave mancante o diversa come nuova fase;
4. applica l’azione al dispositivo;
5. salva la fase soltanto dopo il successo;
6. se la fase non cambia, conserva una scelta recente rilevata dalla memoria eventi.

```yaml
- variables:
    fase_calcolata: >-
      {{ 'ombra' if states('sensor.livello_esempio') | float(0) > 50
         else 'aperto' }}

- action: entity_memory.get_register
  data:
    key: tapparella_esempio.fase_solare
  response_variable: memoria_fase

- variables:
    fase_cambiata: >-
      {{ not memoria_fase.found
         or memoria_fase.value != fase_calcolata }}

# Esegui qui l'azione sul dispositivo.

- if:
    - condition: template
      value_template: "{{ fase_cambiata }}"
  then:
    - action: entity_memory.set_register
      data:
        key: tapparella_esempio.fase_solare
        value: "{{ fase_calcolata }}"
      response_variable: fase_salvata
```

Un registro mancante indica inizializzazione, non un cambiamento fisico. L’automazione deve scegliere esplicitamente se applicare subito la fase o limitarsi a salvarla.

## Scelta manuale fino al prossimo evento

Per la regola “la posizione manuale resta fino al prossimo evento programmato”:

1. deriva la fase programmata corrente;
2. confrontala con l’ultima fase applicata salvata nel registro;
3. se cambia, applica la nuova azione e salva la fase;
4. se non cambia, consulta la memoria eventi e conserva un cambiamento recente non automatizzato o incerto;
5. valuta sempre prima i vincoli assoluti.

Questo funziona anche con tapparelle a ovest e orari non prevedibili: rappresenta la condizione solare come fase (`ombra`, `aperto`, ecc.). Il superamento della soglia diventa il successivo evento programmato. Un trigger ogni cinque o dieci minuti può valutare tutte le fasi in una sola automazione.

Non usare il tempo trascorso dall’ultima esecuzione come sostituto del cambio di fase: un riavvio o un sensore temporaneamente indisponibile non deve fabbricare un nuovo evento.

`compare_register` non scrive. Confronta, esegui l’azione esterna e salva dopo, così un’azione fallita non viene ricordata come riuscita.

Per scritture concorrenti, passa a `set_register` la revisione restituita da `get_register`. La revisione `0` richiede che la chiave sia assente. Un conflitto lascia il valore intatto e deve essere gestito senza tentativi infiniti.

`expected_revision` accetta un intero non negativo o una stringa di sole cifre. Rifiuta booleani, negativi, decimali e stringhe non numeriche. `compare_register` accetta soltanto `key` e `value`.

Per limiti e risposte complete consulta [Registri persistenti](PERSISTENT_REGISTERS.it.md).

## Oggetto evento e contratti

Un evento può contenere:

- `entity_id`, `timestamp`, `old_state`, `new_state`;
- `old_attributes`, `new_attributes`, `changes`;
- `origin`, `confidence`, `matched_service`;
- `context_id`, `parent_id`, `user_id` quando disponibili.

Valori assenti o nulli sono normali. Controlla `memory.event is none` prima di leggere i campi.

Nomi delle azioni, contenitori delle risposte, ordinamento, revisioni e risposte per dati mancanti sono contratti pubblici stabili. Origine, confidenza, identificativi e `matched_service` sono osservazioni best effort e possono essere nulli o meno precisi dopo un ripristino Recorder o una conferma ritardata.

## Origini e confidenza

- `automation`: attribuito a un’automazione tramite il contesto di Home Assistant.
- `authenticated_command`: comando associato a un utente Home Assistant; non identifica dashboard, app o assistente vocale.
- `external_or_physical`: nessun comando Home Assistant corrispondente; può essere fisico o provenire da un’integrazione esterna.
- `device_observation`: cambiamento osservato di un sensore.
- `unknown`: dati insufficienti, soprattutto dopo il ripristino dal Recorder.

`high`, `medium` e `low` descrivono la certezza dell’attribuzione, non l’accuratezza dello stato. Non dedurre mai persona, client o produttore da tempi, nomi o trace vicini. `unknown` non dimostra un intervento umano.

## Schema decisionale prudente

Quando un’automazione potrebbe sovrascrivere una scelta recente:

1. interroga l’ultimo evento rilevante in una finestra limitata;
2. continua se non esiste;
3. consenti un precedente evento automatizzato compatibile;
4. blocca o chiedi conferma per eventi recenti `authenticated_command`, `external_or_physical` o `unknown`;
5. mantieni vincoli di sicurezza separati e prioritari.

Per un vincolo assoluto, soddisfa prima il vincolo e usa la memoria soltanto per scegliere tra le azioni ancora consentite.

## Checklist per YAML generato

Prima di presentare un’automazione verifica che:

- tutti gli ID siano forniti dall’utente o chiaramente segnaposto;
- ogni azione con risposta abbia `response_variable`;
- i template gestiscano `event: null`, `found: false` e campi best effort mancanti;
- il registro venga salvato solo dopo il successo dell’azione esterna;
- conflitti e inizializzazione abbiano una politica esplicita;
- i vincoli assoluti non possano essere aggirati dalla memoria;
- `unknown` ed `external_or_physical` non siano descritti come certamente manuali;
- frequenza di polling e modalità (`single`, `restart`, `queued`, `parallel`) siano deliberate;
- rollback e pulizia indichino il namespace dei registri usato.

Se un’informazione mancante cambia sostanzialmente il comportamento, chiedila all’utente.

## Configurazione, privacy e diagnostica

L’entità interrogata deve essere selezionata direttamente o tramite wildcard. Le wildcard decidono cosa osservare; le azioni devono comunque indicare le entità concrete. Pattern troppo ampi aumentano memoria e lavoro del Recorder.

La diagnostica contiene conteggi aggregati, dimensioni, limiti e versione del formato. Non contiene ID entità, chiavi o valori dei registri, ID utenti o contesti. Log e trace generali di Home Assistant non hanno necessariamente le stesse garanzie e vanno anonimizzati.
