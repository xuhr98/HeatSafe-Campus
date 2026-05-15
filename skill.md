# HeatSafe Campus MVP Development Skill

## Project Goal

Build a minimal, demo-ready Streamlit MVP for **HeatSafe Campus**, an AI-powered heat risk alert system for schools.

The MVP is for a UNICEF Venture Fund prototype application, not a production SaaS product.

Core user flow:

1. User enters/selects school and city
2. App gets or simulates 7-day weather data
3. App calculates child-specific heat risk levels
4. App displays a dashboard
5. App generates role-specific guidance for teachers, parents, and school nurses

## Absolute Scope Limit

This project must stay small enough to complete within approximately 40 hours.

Do NOT build:

- User login
- Database
- Admin panel
- Payment system
- WeChat integration
- Real school database
- GIS map
- Multi-tenant SaaS architecture
- Docker deployment
- Complex backend
- Mobile app
- Complex AI model training
- Medical diagnosis features

This is a prototype demo, not a production system.

## Tech Stack

Use:

- Python
- Streamlit
- Pandas
- Plotly
- Requests
- Open-Meteo API if live weather data is needed

Avoid:

- React
- Next.js
- FastAPI
- Django
- Flask
- Docker
- SQL databases
- Authentication libraries

## File Structure

Keep the project simple:

```text
heatsafe-campus/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
└── screenshots/