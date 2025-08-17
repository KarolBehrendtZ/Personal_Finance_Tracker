# Personal Finance Tracker

Self-hosted aplikacja do zarządzania budżetem osobistym w Dockerze z API w Go i analityką w Pythonie.

## 🚀 Funkcje

- **Backend API w Go** - REST API z autoryzacją JWT
- **Baza danych PostgreSQL** - Relacyjny model danych
- **ETL w Pythonie** - Import transakcji z CSV/JSON, automatyczne kategoryzowanie
- **Analityka wydatków** - Wykrywanie nietypowych wzorców, analizy trendów
- **Docker Compose** - Pełna konteneryzacja
- **Nginx Proxy** - Reverse proxy z load balancingiem
- **Opcjonalny dashboard** - Streamlit UI (planowane rozszerzenie)

## 📋 Wymagania

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 5GB miejsca na dysku

## 🛠️ Instalacja

1. **Sklonuj repozytorium**
```bash
git clone <repo-url>
cd personal-finance-tracker
```

2. **Skonfiguruj środowisko**
```bash
cp .env.example .env
# Edytuj .env i zmień JWT_SECRET oraz inne ustawienia
```

3. **Uruchom aplikację**
```bash
chmod +x scripts/*.sh
./scripts/setup.sh
```

## 📊 Struktura Projektu

```
project/
├── cmd/api/                 # Go API main
├── internal/
│   ├── handlers/           # HTTP handlers
│   ├── models/            # Data models
│   ├── database/          # DB connection
│   └── auth/              # JWT auth
├── migrations/            # SQL migrations
├── python/
│   ├── etl/              # ETL scripts
│   └── analytics/        # Analityka
├── scripts/              # Bash scripts
├── configs/              # Nginx config
└── docker-compose.yml    # Container orchestration
```

## 🔌 API Endpoints

### Autoryzacja
- `POST /api/v1/auth/register` - Rejestracja
- `POST /api/v1/auth/login` - Logowanie

### Konta
- `GET /api/v1/accounts` - Lista kont
- `POST /api/v1/accounts` - Nowe konto
- `PUT /api/v1/accounts/:id` - Aktualizacja konta
- `DELETE /api/v1/accounts/:id` - Usunięcie konta

### Kategorie
- `GET /api/v1/categories` - Lista kategorii
- `POST /api/v1/categories` - Nowa kategoria
- `PUT /api/v1/categories/:id` - Aktualizacja kategorii

### Transakcje
- `GET /api/v1/transactions` - Lista transakcji
- `POST /api/v1/transactions` - Nowa transakcja
- `POST /api/v1/transactions/bulk` - Import CSV

### Analityka
- `GET /api/v1/analytics/summary` - Podsumowanie
- `GET /api/v1/analytics/spending` - Analiza wydatków

## 🐍 Python ETL

### Import transakcji z CSV
```python
from python.etl.transaction_importer import TransactionImporter

importer = TransactionImporter()
importer.import_csv('bank_export.csv', user_id=1, account_id=1)
importer.auto_categorize_transactions(user_id=1)
```

### Analiza wydatków
```python
from python.analytics.spending_analyzer import SpendingAnalyzer

analyzer = SpendingAnalyzer()
unusual = analyzer.detect_unusual_spending(user_id=1)
trends = analyzer.analyze_spending_trends(user_id=1)
report = analyzer.generate_spending_report(user_id=1)
```

## 🔧 Zarządzanie

### Uruchomienie
```bash
./scripts/setup.sh
```

### Zatrzymanie
```bash
./scripts/stop.sh
```

### Logi
```bash
./scripts/logs.sh [service_name]
```

### Backup bazy danych
```bash
./scripts/backup.sh
```

### Reset (USUWA WSZYSTKIE DANE!)
```bash
./scripts/reset.sh
```

## 🌐 Dostęp do Usług

- **API**: http://localhost:8080
- **Nginx Proxy**: http://localhost
- **Dashboard**: http://localhost:8501 (jeśli włączony)
- **Baza danych**: localhost:5432

## 📝 Model Danych

### Główne tabele:
- `users` - Użytkownicy
- `accounts` - Konta bankowe
- `categories` - Kategorie transakcji
- `transactions` - Transakcje
- `budget_rules` - Reguły budżetowe

## 🔐 Bezpieczeństwo

1. **Zmień JWT_SECRET** w pliku .env
2. **Użyj HTTPS** w produkcji
3. **Ustaw silne hasła** do bazy danych
4. **Regularnie rób backupy**

## 🚧 Planowane Rozszerzenia

- [ ] Streamlit Dashboard
- [ ] Automatyczne tagowanie wydatków (regex + ML)
- [ ] Integracja z cronem dla raportów
- [ ] API do podłączania banków
- [ ] Mobilna aplikacja
- [ ] Powiadomienia o przekroczeniu budżetu

## 🐳 Docker Services

- **postgres** - Baza danych PostgreSQL 15
- **api** - Go backend API
- **etl_worker** - Python ETL worker
- **nginx** - Reverse proxy
- **dashboard** - Streamlit UI (opcjonalny)

## 📚 Wykorzystane Technologie

- **Backend**: Go 1.21, Gin, JWT, PostgreSQL
- **Analytics**: Python 3.11, Pandas, NumPy, Psycopg2
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Database**: PostgreSQL 15 z migracja SQL

## 🤝 Contribucja

1. Fork repozytorium
2. Stwórz branch z feature
3. Commit zmiany
4. Push do brancha
5. Otwórz Pull Request

## 📄 Licencja

MIT License - szczegóły w pliku LICENSE
