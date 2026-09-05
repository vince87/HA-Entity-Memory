# Esempio: rispettare una scelta recente sul climatizzatore

[English](EXAMPLE_CLIMATE_AUTOMATION.md) · **Italiano**

Quando la temperatura supera 27 °C, questa automazione controlla l’ultimo evento e non riaccende il climatizzatore se lo spegnimento recente potrebbe essere una scelta esterna all’automazione.

Sostituisci gli ID e le temperature. È un esempio comportamentale, non un controllo di sicurezza.

```yaml
alias: Esempio - raffresca rispettando lo spegnimento recente
description: Rispetta l'ultima decisione ricordata sul climatizzatore.
triggers:
  - trigger: numeric_state
    entity_id: sensor.temperatura_stanza_esempio
    above: 27

conditions:
  - condition: state
    entity_id: climate.climatizzatore_esempio
    state: "off"

actions:
  - action: entity_memory.last_event
    data:
      entity_id:
        - climate.climatizzatore_esempio
      since: "02:00:00"
    response_variable: memoria_clima

  - condition: template
    alias: Continua salvo uno spegnimento recente non automatizzato
    value_template: >-
      {{ memoria_clima.event is none
         or memoria_clima.event.new_state != 'off'
         or memoria_clima.event.origin == 'automation' }}

  - action: climate.set_temperature
    target:
      entity_id: climate.climatizzatore_esempio
    data:
      hvac_mode: cool
      temperature: 24

mode: single
```

La logica è volutamente prudente:

- senza eventi ricordati l’automazione può continuare;
- uno spegnimento recente dell’automazione può essere superato;
- uno spegnimento `authenticated_command`, `external_or_physical` o `unknown` impedisce il riavvio;
- `since` stabilisce per quanto tempo rispettare la decisione.

Gli eventi recuperati dal Recorder possono essere `unknown` con confidenza bassa. Trattarli con prudenza evita di annullare silenziosamente una possibile decisione umana dopo un riavvio.
