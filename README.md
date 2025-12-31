# Waste Collection Calendar – Sandnes Kommune

Home Assistant integration that fetches your personal waste collection calendar for **Sandnes kommune (Norway)** directly from **hentavfall.no**.

The integration parses the official municipal calendar and exposes pickup dates as entities in Home Assistant, making it easy to build automations, reminders, and dashboards.

---

## Features

- One sensor per waste type showing next pickup date
- One combined calendar sensor with upcoming pickups
- Binary sensor for pickup today
- Binary sensor for pickup tomorrow
- All entities grouped under one device
- Supports automations and notifications
- UI setup via Home Assistant (Config Flow)
- Fully compatible with HACS

---

## Installation

Install via **HACS** as a custom integration.

1. Add this repository as a custom repository in HACS
2. Install the integration
3. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Select **Waste Collection Calendar – Sandnes Kommune**
4. Paste your personal waste calendar URL from `hentavfall.no`

---

## Where do I find the URL?

1. Go to  
   https://www.hentavfall.no/rogaland/sandnes/tommekalender/
2. Search for your address
3. Open your waste calendar
4. Copy the full URL from the browser address bar

### Example URL

https://www.hentavfall.no/rogaland/sandnes/tommekalender/show?id=XXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX&municipality=Sandnes%20kommune&gnumber=CC&bnumber=XXXX&snumber=0

### URL parameters explained

- `id` = Unique identifier for your address
- `municipality` = Municipality name (Sandnes kommune)
- `gnumber` = Gårdsnummer
- `bnumber` = Bruksnummer
- `snumber` = Seksjonsnummer (usually 0)

This URL is personal to your address and ensures correct pickup dates.

---

## Entities created

### 📅 Calendar sensor

**`sensor.tommekalender_kalender`**

- State shows the date of the next upcoming pickup
- Attributes:
  - `upcoming`: list of the next 5 pickup dates with waste types
  - `next_types`: waste types collected on the next pickup date
  - `source_url`: original hentavfall.no calendar URL

---

### 🗑️ Waste type sensors

Each sensor shows the **next pickup date** for that waste type.

- `sensor.tommekalender_restavfall`
- `sensor.tommekalender_matavfall`
- `sensor.tommekalender_papir`
- `sensor.tommekalender_plastemballasje`
- `sensor.tommekalender_juletre`

---

### ✅ Binary sensors

- `binary_sensor.tommekalender_tomming_i_dag`
- `binary_sensor.tommekalender_tomming_i_morgen`

These sensors turn **on/off automatically** based on actual pickup days and are ideal for automations.

---

## Automation examples

### 🔔 Notify the evening before pickup (recommended)

Send a notification at 20:00 **only if there is waste collection tomorrow**.

```yaml
automation:
  - alias: "Waste pickup reminder (evening before)"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.tommekalender_tomming_i_morgen
        state: "on"
    action:
      - service: notify.notify
        data:
          title: "Waste collection"
          message: "Waste will be collected tomorrow."
🧠 Advanced notification with waste types
Uses the calendar sensor to show what is collected tomorrow and the next pickup after tomorrow.
automation:
  - alias: "Waste pickup details (evening before)"
    trigger:
      - platform: time
        at: "20:00:00"
    variables:
      upcoming: "{{ state_attr('sensor.tommekalender_kalender', 'upcoming') | default([], true) }}"
      tomorrow: "{{ (now() + timedelta(days=1)).date().isoformat() }}"
      tomorrow_item: "{{ upcoming | selectattr('date','equalto',tomorrow) | list | first }}"
      tomorrow_types: "{{ tomorrow_item.types if tomorrow_item is not none else [] }}"
    condition:
      - condition: template
        value_template: "{{ tomorrow_types | length > 0 }}"
    action:
      - service: notify.notify
        data:
          title: "Waste collection tomorrow"
          message: >-
            Tomorrow:
            - {{ tomorrow_types | join('\n- ') }}
🧹 Conditional automation by waste type
Trigger actions only for specific waste types.
condition:
  - condition: template
    value_template: >
      {{ 'Plastemballasje' in state_attr('sensor.tommekalender_kalender','next_types') }}
Useful for:
Extra reminders
Light or display changes
Dashboard indicators
📆 Weekly waste summary
Send a weekly overview of upcoming waste collection.
automation:
  - alias: "Weekly waste summary"
    trigger:
      - platform: time
        at: "09:00:00"
        weekday:
          - mon
    action:
      - service: notify.notify
        data:
          title: "Waste collection – upcoming"
          message: >
            {% for item in state_attr('sensor.tommekalender_kalender','upcoming') %}
            {{ item.date }}:
            - {{ item.types | join(', ') }}
            {% endfor %}
Calendar & Dashboard usage
📊 Show next pickup in the UI
Example Markdown card:
type: markdown
content: >
  **Next waste collection:**  
  {{ states('sensor.tommekalender_kalender') }}

  **Types:**  
  {{ state_attr('sensor.tommekalender_kalender','next_types') | join(', ') }}
Works well with:
Entities cards
Markdown cards
Mushroom cards
Custom dashboards
Best practices
Use binary sensors to decide when something happens
Use calendar sensor attributes to decide what happens
Avoid hardcoding dates — the integration handles year changes automatically
Automations continue to work across month and year boundaries
Notes
Data is fetched periodically from hentavfall.no
Temporary network issues may mark entities as unavailable
Entities recover automatically when data is available again
The integration automatically handles year changes and calendar rollovers
