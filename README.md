Waste Collection Calendar – Sandnes Kommune

Home Assistant integration that fetches your personal waste collection calendar for Sandnes kommune (Norway) directly from hentavfall.no.

The integration parses the official municipal calendar and exposes pickup dates as entities in Home Assistant.

Features:
- One sensor per waste type showing next pickup date
- One combined calendar sensor with upcoming pickups
- Binary sensor for pickup today
- Binary sensor for pickup tomorrow
- All entities grouped under one device
- Supports automations and notifications
- UI setup via Home Assistant (Config Flow)
- Fully compatible with HACS

Installation:
Install via HACS as a custom integration.
Restart Home Assistant after installation.

Setup:
Go to Settings → Devices & Services
Click Add Integration
Select Waste Collection Calendar – Sandnes Kommune
Paste your personal waste calendar URL from hentavfall.no

Where do I find the URL?
1. Go to https://www.hentavfall.no/rogaland/sandnes/tommekalender/
2. Search for your address
3. Open your waste calendar
4. Copy the full URL from the browser address bar

Example URL:
https://www.hentavfall.no/rogaland/sandnes/tommekalender/show?id=XXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX&municipality=Sandnes%20kommune&gnumber=CC&bnumber=XXXX&snumber=0

URL parameters explained:
id = Unique identifier for your address
municipality = Municipality name (Sandnes kommune)
gnumber = Gårdsnummer
bnumber = Bruksnummer
snumber = Seksjonsnummer (usually 0)

This URL is personal to your address and ensures correct pickup dates.

Entities created:

Calendar sensor:
sensor.tommekalender_kalender
State shows the date of the next upcoming pickup.
Attributes include:
- upcoming: list of the next 5 pickup dates with waste types
- next_types: waste types collected on the next pickup date
- source_url: original hentavfall.no calendar URL

Waste type sensors:
sensor.tommekalender_restavfall
sensor.tommekalender_matavfall
sensor.tommekalender_papir
sensor.tommekalender_plastemballasje
sensor.tommekalender_juletre

Each sensor shows the next pickup date for that waste type.

Binary sensors:
binary_sensor.tommekalender_tomming_i_dag
binary_sensor.tommekalender_tomming_i_morgen

These can be used for simple automations and notifications.

Automation examples:
- Notify the evening before pickup
- Show next pickup on dashboard
- Conditional automations based on waste type
- Weekly waste summary

Notes:
The integration automatically handles year changes.
Data is fetched periodically from hentavfall.no.
Temporary network issues may mark entities unavailable, but they recover automatically.
