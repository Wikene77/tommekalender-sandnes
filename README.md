Waste Collection Calendar – Sandnes Kommune
A Home Assistant integration that fetches your personal waste collection calendar
for Sandnes kommune (Norway) directly from hentavfall.no.
The integration parses the official municipal calendar and exposes the data as
date-based sensors in Home Assistant.
Features
One sensor per waste type (next pickup date)
One combined calendar sensor with upcoming pickups
Two helper binary sensors:
Pickup today
Pickup tomorrow
All entities grouped under one device
Supports automations and notifications
UI setup via Home Assistant (Config Flow)
Fully compatible with HACS
Installation (HACS)
Open HACS → Integrations
Click ⋮ → Custom repositories
Add the repository:
https://github.com/Wikene77/tommekalender-sandnes
Select Category: Integration
Install Waste Collection Calendar – Sandnes
Restart Home Assistant
Setup
Go to Settings → Devices & Services
Click Add Integration
Select Waste Collection Calendar – Sandnes
Paste your personal waste calendar URL from hentavfall.no
Where do I find the URL?
Go to
https://www.hentavfall.no/rogaland/sandnes/tommekalender/
Search for your address
Open your calendar
Copy the full URL from the browser address bar
Example URL
https://www.hentavfall.no/rogaland/sandnes/tommekalender/show
?id=XXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX
&municipality=Sandnes%20kommune
&gnumber=CC
&bnumber=XXXX
&snumber=0
URL parameters explained
Parameter	Description
id	Unique identifier for your address
municipality	Municipality name (Sandnes kommune)
gnumber	Gårdsnummer
bnumber	Bruksnummer
snumber	Seksjonsnummer (usually 0)
💡 This URL is personal to your address and ensures correct pickup dates.
Sensors
The integration creates the following entities.
Calendar Sensor
Entity
sensor.tommekalender_kalender
State
Date of the next upcoming pickup (any waste type)
Attributes
upcoming
List of the next 5 upcoming pickups, each containing:
date – pickup date (YYYY-MM-DD)
types – list of waste types collected that day
next_types
Waste types collected on the next pickup date
source_url
Original hentavfall.no calendar URL
Waste Type Sensors
Each waste fraction gets its own date sensor:
sensor.tommekalender_restavfall
sensor.tommekalender_matavfall
sensor.tommekalender_papir
sensor.tommekalender_plastemballasje
sensor.tommekalender_juletre
State
Date of the next pickup for that waste type
Attributes
type
Waste type name (e.g. Restavfall)
upcoming
The next 5 upcoming pickups (same structure as calendar sensor)
source_url
Original hentavfall.no calendar URL
Pickup Binary Sensors
These are simple helper sensors (very handy for automations):
binary_sensor.tommekalender_tomming_i_dag
binary_sensor.tommekalender_tomming_i_morgen
State
on if one or more waste types are collected that day
off if there is no pickup
Attributes
date – the date checked (YYYY-MM-DD)
types – list of waste types collected that day (empty if none)
source_url – original calendar URL
All entities are grouped under a single device in Home Assistant.
Automations
Example: Notify only when there is pickup tomorrow
{{ is_state('binary_sensor.tommekalender_tomming_i_morgen', 'on') }}
Message example:
I morgen hentes: {{ state_attr('binary_sensor.tommekalender_tomming_i_morgen', 'types') | join(', ') }}
Example use cases:
Notify the evening before pickup
Show “pickup tomorrow” on dashboard
Conditional automations based on waste type
Notes
The integration automatically handles year changes (e.g. December → January)
The calendar is fetched periodically from hentavfall.no
Temporary network issues may briefly mark entities as unavailable, but they recover automatically
