# HeatSafe Campus

**AI-assisted heat health early warning for schools and children**

HeatSafe Campus is a lightweight **prototype** Streamlit application for climate-aware planning in school settings. It combines public weather and air-quality data with rule-based risk logic and optional AI-generated role guidance—intended for **demonstration, education, and early design feedback** (e.g. UNICEF-style venture or research contexts), not as a regulated or clinical system.

---

## Features

- **Weather** — Seven-day forecast via [Open-Meteo](https://open-meteo.com/) with mock fallback when the API is unavailable.
- **Air quality** — Optional daily-max PM2.5, PM10, ozone, and US AQI aggregated from Open-Meteo’s air-quality API; risk scoring can incorporate high AQI when data is present.
- **Geolocation** — City lookup (predefined coordinates or Open-Meteo Geocoding); optional **school** geocoding in China via **Amap** when configured.
- **Map** — Simple school marker map (Folium) when Amap resolves the school successfully.
- **Risk model** — Explainable rule-based score from temperature, humidity, school type, outdoor activity plan, and AQI thresholds.
- **Guidance** — Bilingual (**中文 / English**) templates; optional **DeepSeek** chat-completion output for teachers, parents, and school nurses, with graceful fallback if the API is missing or fails.
- **UI** — Single-page Streamlit layout with dashboards, charts, and guidance cards.

---

## Tech stack

| Layer | Choices |
|--------|---------|
| App | Python, [Streamlit](https://streamlit.io/) |
| Data | [Pandas](https://pandas.pydata.org/) |
| Charts | [Plotly](https://plotly.com/python/) |
| Map | [Folium](https://python-visualization.github.io/folium/), [streamlit-folium](https://github.com/randyzwitch/streamlit-folium) |
| HTTP | [Requests](https://requests.readthedocs.io/) |

---

## APIs used

| Service | Purpose |
|---------|---------|
| **Open-Meteo Forecast** | Temperature, humidity, UV, apparent temperature |
| **Open-Meteo Air Quality** | Hourly pollutants → daily max columns |
| **Open-Meteo Geocoding** | City coordinates when not using built-in presets |
| **Amap REST (Geocode)** | Optional address → coordinates for Chinese schools |
| **DeepSeek** | Optional OpenAI-compatible chat completions for guidance text |

Third-party Terms of Use and attribution apply per each provider’s documentation.

---

## Installation

```bash
git clone <your-repo-url>
cd heatsafe-campus
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Environment variables

All keys are **optional** except where you enable the matching feature:

| Variable | Enables |
|----------|---------|
| `DEEPSEEK_API_KEY` | AI-generated guidance (toggle in the app) |
| `AMAP_API_KEY` | Amap school geocoding and the school location map |

**Example (do not commit real secrets):**

```bash
# Optional — DeepSeek (OpenAI-compatible endpoint)
export DEEPSEEK_API_KEY="your-deepseek-key"

# Optional — Amap Web Service key (China school geocode)
export AMAP_API_KEY="your-amap-key"
```

On Windows (PowerShell):

```powershell
$env:DEEPSEEK_API_KEY = "your-deepseek-key"
$env:AMAP_API_KEY = "your-amap-key"
```

---

## Run locally (Streamlit)

```bash
streamlit run app.py
```

The app opens in your browser (default [http://localhost:8501](http://localhost:8501)).

### Deployment notes

- Deploy like any Streamlit app (e.g. [Streamlit Community Cloud](https://streamlit.io/cloud), internal VM, or container with `streamlit run app.py`).
- Set environment variables in the host’s secret management; never embed keys in `app.py` or the README.
- Ensure outbound HTTPS access to Open-Meteo, and—if used—Amap and DeepSeek endpoints.

---

## Project structure

```text
heatsafe-campus/
├── app.py              # Streamlit entry point (layout and main flow)
├── config.py           # API URLs, env helpers, shared constants
├── text_strings.py     # Bilingual UI strings and templates
├── geocoding.py        # City aliases, Open-Meteo and Amap geocoding
├── weather.py          # Forecast, air quality, and data loading
├── risk.py             # Risk score and level helpers
├── guidance.py         # Rule-based and DeepSeek role guidance
├── parent_notice.py    # Parent notice generator
├── student_health.py   # Student heat-health AI assistant
├── map_utils.py        # Folium school map
├── ui_components.py    # CSS, charts, metric cards, formatters
├── requirements.txt    # Python dependencies
├── LICENSE             # MIT License
├── README.md           # This file
├── skill.md            # Internal MVP scope notes (optional)
└── screenshots/        # Optional demo images
```

---

## Disclaimer

This tool is an **early prototype**. Forecasts and indices come from third-party models and APIs; accuracy and availability are **not guaranteed**. Outputs are meant to support **planning awareness and health education**, not operational emergency response on their own.

---

## Educational & prototype disclaimer

HeatSafe Campus is designed for **learning, prototyping, and stakeholder demos**. It:

- Does **not** provide medical diagnosis, treatment, or individualized clinical advice  
- Does **not** replace national or local meteorological authorities, pollution indices, or school safety policies  
- Has **not** been validated as a production decision system for heat emergencies  

Always follow official guidance from health authorities and your school jurisdiction. Maintain clear attribution when using external data sources.

---

© 2026 Beijing Changqianyue Environmental Technology Co., Ltd.  
Licensed under the MIT License — see [LICENSE](LICENSE).
