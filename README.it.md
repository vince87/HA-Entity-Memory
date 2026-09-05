<p align="center">
  <img src="https://raw.githubusercontent.com/vince87/HA-Entity-Memory/main/custom_components/entity_memory/brand/icon%402x.png" alt="Entity Memory" width="180">
</p>

<h1 align="center">Entity Memory</h1>

<p align="center">Memoria persistente e attenta alla privacy per le automazioni di Home Assistant.</p>

<p align="center">
  <a href="https://github.com/vince87/HA-Entity-Memory/releases"><img alt="Release" src="https://img.shields.io/github/v/release/vince87/HA-Entity-Memory?style=flat-square"></a>
  <a href="https://github.com/vince87/HA-Entity-Memory/actions"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/vince87/HA-Entity-Memory/validate.yml?branch=main&style=flat-square&label=validation"></a>
  <a href="https://www.hacs.xyz/"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square"></a>
  <a href="LICENSE"><img alt="Licenza" src="https://img.shields.io/github/license/vince87/HA-Entity-Memory?style=flat-square"></a>
</p>

<p align="center"><a href="README.md">English</a> · <strong>Italiano</strong></p>

Entity Memory aggiunge due tipi di memoria senza creare entità helper visibili:

- **Memoria degli eventi:** conserva i cambiamenti significativi recenti di luci, tapparelle, climatizzatori, interruttori e sensori binari, attribuendone prudentemente l’origine.
- **Registri persistenti:** conservano piccoli valori, flag, fasi e checkpoint appartenenti alle automazioni anche dopo ricaricamenti e riavvii.

Risponde a domande come “questo dispositivo è stato modificato di recente fuori dalla mia automazione?” e “siamo ancora nella stessa fase programmata?”.

> [!IMPORTANT]
> Entity Memory aiuta a decidere, ma non è un sistema di sicurezza. Antifurto, serrature, incendio, pioggia, vento, gelo e altri vincoli assoluti devono restare normali condizioni di Home Assistant e avere sempre la precedenza sulle preferenze ricordate.

## Caratteristiche

- Configurazione dall’interfaccia di Home Assistant
- Entità esplicite e pattern wildcard come `cover.*`
- Ripristino degli eventi tramite Recorder
- Attribuzione prudente dell’origine e della confidenza
- Azioni con risposta pensate per le automazioni
- Registri JSON invisibili con revisioni e concorrenza ottimistica
- Diagnostica aggregata rispettosa della privacy
- Interfaccia in inglese, italiano, tedesco, francese, spagnolo e portoghese

## Installazione

### HACS

1. In HACS aggiungi `https://github.com/vince87/HA-Entity-Memory` come repository personalizzato di tipo **Integrazione**.
2. Scarica l’ultima release stabile.
3. Riavvia Home Assistant.
4. Apri **Impostazioni → Dispositivi e servizi → Aggiungi integrazione** e scegli **Entity Memory**.

### Manuale

Copia `custom_components/entity_memory` in `/config/custom_components/entity_memory`, riavvia Home Assistant e aggiungi l’integrazione da **Impostazioni → Dispositivi e servizi**.

Richiede Home Assistant `2026.1.0` o successivo. Recorder è necessario per ripristinare lo storico degli eventi all’avvio.

## Primi passi

Scegli entità specifiche, pattern wildcard o entrambi. Usa la selezione più ristretta adatta allo scopo.

```text
light.cucina
cover.*
binary_sensor.*_finestra
```

Verifica se esiste un cambiamento recente rilevante:

```yaml
- action: entity_memory.was_changed
  data:
    entity_id:
      - light.cucina
    since: "00:30:00"
    origins:
      - authenticated_command
      - external_or_physical
      - unknown
  response_variable: memoria

- condition: template
  value_template: "{{ not memoria.found }}"
```

Ricorda una fase dell’automazione tra esecuzioni e riavvii:

```yaml
- action: entity_memory.set_register
  data:
    key: tapparelle.ovest.fase
    value: ombra
  response_variable: salvataggio
```

## Azioni disponibili

| Memoria eventi | Registri persistenti |
|---|---|
| `get_events` | `get_register` |
| `last_event` | `set_register` |
| `was_changed` | `compare_register` |
| `count_events` | `delete_register` |
| | `list_registers` |

Le azioni restituiscono dati e normalmente vanno chiamate con `response_variable`.

## Documentazione

| Italiano | English |
|---|---|
| [Guida per automazioni IA](docs/AI_AUTOMATION_GUIDE.it.md) | [AI automation guide](docs/AI_AUTOMATION_GUIDE.md) |
| [Registri persistenti](docs/PERSISTENT_REGISTERS.it.md) | [Persistent registers](docs/PERSISTENT_REGISTERS.md) |
| [Schemi di automazione](docs/AUTOMATION_PATTERNS.it.md) | [Automation patterns](docs/AUTOMATION_PATTERNS.md) |
| [Esempio climatizzazione](docs/EXAMPLE_CLIMATE_AUTOMATION.it.md) | [Climate example](docs/EXAMPLE_CLIMATE_AUTOMATION.md) |

Consulta le [note di rilascio](RELEASE_NOTES.md) per modifiche e compatibilità.

## Limiti dell’attribuzione

L’attribuzione è volutamente prudente. `authenticated_command` dimostra che Home Assistant ha associato il comando a un utente, non se provenga da dashboard, app o assistente vocale. `external_or_physical` può indicare anche un’integrazione esterna. Gli eventi ripristinati dal Recorder possono essere `unknown` con confidenza bassa.

## Privacy e assistenza

La diagnostica esclude ID delle entità, chiavi e valori dei registri, ID utente e ID di contesto. Log generali e trace delle automazioni vanno comunque anonimizzati prima della condivisione.

Per segnalare un problema indica la versione di Entity Memory e di Home Assistant, i passaggi anonimizzati e la diagnostica già controllata nell’[issue tracker](https://github.com/vince87/HA-Entity-Memory/issues).

## Licenza

[MIT](LICENSE)
