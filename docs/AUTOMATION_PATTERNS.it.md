# Schemi di automazione

[English](AUTOMATION_PATTERNS.md) · **Italiano**

Questi frammenti anonimi mostrano il contratto delle azioni. Sostituisci gli ID di esempio e adatta le finestre temporali. Sono schemi decisionali, non controlli di sicurezza.

## Tapparella: conserva una posizione recente incerta

```yaml
- action: entity_memory.last_event
  data:
    entity_id:
      - cover.tapparella_esempio
    since: "04:00:00"
    origins:
      - authenticated_command
      - external_or_physical
      - unknown
  response_variable: memoria_tapparella

- condition: template
  value_template: "{{ memoria_tapparella.event is none }}"
```

Usalo soltanto nella fase programmata corrente. Una nuova fascia oraria o fase solare può superare la scelta precedente. Antifurto e vincoli meteo assoluti vanno controllati prima.

## Luce: agisci solo senza comandi recenti esterni all’automazione

```yaml
- action: entity_memory.was_changed
  data:
    entity_id:
      - light.stanza_esempio
    since: "00:30:00"
    origins:
      - authenticated_command
      - external_or_physical
      - unknown
  response_variable: memoria_luce

- condition: template
  value_template: "{{ not memoria_luce.found }}"
```

Questa regola prudente considera anche un’origine ambigua come motivo per aspettare.

## Porta: conta le aperture

```yaml
- action: entity_memory.count_events
  data:
    entity_id:
      - binary_sensor.porta_esempio
    since: "01:00:00"
    to_state: "on"
  response_variable: memoria_porta

- condition: template
  value_template: "{{ memoria_porta.count >= 3 }}"
```

Controlla sempre la `device_class`: `on` e `off` non significano necessariamente aperto e chiuso per ogni sensore binario.

## PIR: ultimo movimento

```yaml
- action: entity_memory.last_event
  data:
    entity_id:
      - binary_sensor.movimento_esempio
    since: "00:10:00"
    to_state: "on"
  response_variable: memoria_movimento

- condition: template
  value_template: "{{ memoria_movimento.event is not none }}"
```

Un evento PIR è un’osservazione del dispositivo: non dimostra identità, durata della presenza o intenzione.

## Più entità

```yaml
- action: entity_memory.get_events
  data:
    entity_id:
      - binary_sensor.porta_esempio
      - binary_sensor.movimento_esempio
    since: "00:15:00"
    limit: 20
  response_variable: memoria_area
```

I risultati sono dal più recente al più vecchio. Gestisci sempre una lista `events` vuota e usa `count` senza presumere che esista un evento.
