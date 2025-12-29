# Waste Collection Calendar – Sandnes

A Home Assistant integration that fetches the waste collection calendar for **Sandnes kommune (Norway)** directly from **hentavfall.no**.

The integration provides:
- One sensor per waste type (next pickup date)
- One combined calendar sensor with upcoming pickups (`upcoming`)
- Support for automations and notifications
- UI setup via Home Assistant (Config Flow)
- Ready for HACS

---

## Installation (HACS)

1. Open **HACS → Integrations**
2. Click **⋮ → Custom repositories**
3. Add the repository: https://github.com/Wikene77/tommekalender-sandnes
4. Select **Category: Integration**
5. Install **Waste Collection Calendar – Sandnes**
6. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Select **Waste Collection Calendar – Sandnes**
4. Paste your personal waste calendar URL from hentavfall.no, for example: https://www.hentavfall.no/rogaland/sandnes/tommekalender/show?...

The URL can be found by searching for your address on: https://www.hentavfall.no/rogaland/sandnes/tommekalender/

---

## Sensors

The integration creates the following sensors:

### Calendar Sensor
- **Calendar**
- State: next pickup date
- Attributes:
 - `upcoming`: list of upcoming pickup dates and waste types
 - `source_url`: original calendar URL

### Waste Type Sensors
Each waste fraction gets its own sensor with device class `date`:
- Restavfall (Residual waste)
- Matavfall (Food waste)
- Papir (Paper)
- Plastemballasje (Plastic packaging)
- Juletre (Christmas tree)

All sensors are grouped under one device in Home Assistant.

---

## Automations

The `upcoming` attribute can be used to create advanced automations, such as:
- Notifications the evening before pickup
- Showing next pickup type and date
- Weekly summaries

Example (Template):
```jinja
{{ state_attr('sensor.tommekalender_sandnes_calendar', 'upcoming') }}
