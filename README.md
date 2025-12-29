# Waste Collection Calendar – Sandnes Kommune

A Home Assistant integration that fetches your **personal waste collection calendar**
for **Sandnes kommune (Norway)** directly from **hentavfall.no**.

The integration parses the official municipal calendar and exposes the data as
date-based sensors in Home Assistant.

---

## Features

- One sensor per waste type (next pickup date)
- One combined calendar sensor with upcoming pickups
- All sensors grouped under one device
- Supports automations and notifications
- UI setup via Home Assistant (Config Flow)
- Fully compatible with HACS

---

## Installation (HACS)

1. Open **HACS → Integrations**
2. Click **⋮ → Custom repositories**
3. Add the repository:

https://github.com/Wikene77/tommekalender-sandnes

4. Select **Category: Integration**
5. Install **Waste Collection Calendar – Sandnes**
6. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Select **Waste Collection Calendar – Sandnes**
4. Paste your personal waste calendar URL from hentavfall.no

### Where do I find the URL?

1. Go to  
https://www.hentavfall.no/rogaland/sandnes/tommekalender/
2. Search for your address
3. Open your calendar
4. Copy the full URL from the browser address bar

### Example URL

https://www.hentavfall.no/rogaland/sandnes/tommekalender/show
?id=XXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX
&municipality=Sandnes%20kommune
&gnumber=CC
&bnumber=XXXX
&snumber=0

### URL parameters explained

| Parameter | Description |
|---------|-------------|
| `id` | Unique identifier for your address |
| `municipality` | Municipality name (Sandnes kommune) |
| `gnumber` | Gårdsnummer |
| `bnumber` | Bruksnummer |
| `snumber` | Seksjonsnummer (usually 0) |

> 💡 This URL is personal to your address and ensures correct pickup dates.

---

## Sensors

The integration creates the following sensors.

### Calendar Sensor

**Sensor name**
sensor.tommekalender_kalender

**State**
- Date of the next upcoming pickup (any waste type)

**Attributes**
- `upcoming`  
  List of the **next 5 upcoming pickups**, each containing:
  - `date` – pickup date (YYYY-MM-DD)
  - `types` – list of waste types collected that day
- `next_types`  
  Waste types collected on the next pickup date
- `source_url`  
  Original hentavfall.no calendar URL

---

### Waste Type Sensors

Each waste fraction gets its own date sensor:

- `sensor.tommekalender_restavfall`
- `sensor.tommekalender_matavfall`
- `sensor.tommekalender_papir`
- `sensor.tommekalender_plastemballasje`
- `sensor.tommekalender_juletre`

**State**
- Date of the next pickup for that waste type

**Attributes**
- `type`  
  Waste type name (e.g. `Restavfall`)
- `upcoming`  
  The next **5 upcoming pickups** (same structure as calendar sensor)
- `source_url`  
  Original hentavfall.no calendar URL

All sensors use device class **`date`** and are grouped under a single device
in Home Assistant.

---

## Automations

The `upcoming` attribute allows advanced automations.

### Example: Notification the evening before pickup

```jinja
{% set upcoming = state_attr('sensor.tommekalender_kalender', 'upcoming') %}
{% if upcoming %}
  Neste tømming {{ upcoming[0].date }}: {{ upcoming[0].types | join(', ') }}
{% endif %}
Example use cases
Notify the evening before pickup
Show next pickup on dashboard
Weekly waste summary
Conditional automations based on waste type
Notes
The integration automatically handles year changes (e.g. December → January)
The calendar is fetched periodically from hentavfall.no
Temporary network issues may briefly mark sensors as unavailable, but they recover automatically
