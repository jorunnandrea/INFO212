# INFO212

Dette er et studentprosjekt ved Universitetet i Bergen (UiB).

## Funksjonalitet

- Henter arrangementer fra Ticketmaster Discovery API
- Bruker FastAPI for å hente og vise arrangementer
- Viser arrangementer for Bergen (eller valgt område) i en enkel HTML-visning
- Støtter oppsett for videre utvidelser som filtrering og søk

## Struktur (foreløpig)
```
fastapi_mvp/
├── app/
│ ├── main.py # FastAPI-app, API-kall og HTML-rendering
│ ├── templates/
│ │ └── home.html # Enkelt GUI som viser arrangementer
│ └── init.py
├── .env # Inneholder API_KEY (blir ikke lastet opp til GIT)
├── .gitignore
├── README.md
└── requirements.txt
```

