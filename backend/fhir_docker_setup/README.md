# FHIR PostgreSQL Docker Setup

This stack gives you:
- **PostgreSQL 16** with the FHIR schema auto-created on first startup
- **pgAdmin 4** for browsing tables and running queries
- an optional **FHIR loader container** to ingest your JSON bundle into Postgres

## Files
- `docker-compose.yml` - full local stack
- `init/01_fhir_schema.sql` - auto-runs when Postgres initializes for the first time
- `loader/` - one-shot Python loader image
- `data/` - place your FHIR bundle JSON here
- `.env.example` - environment variables to copy into `.env`

## 1) Prepare
Copy `.env.example` to `.env`.

Put your FHIR bundle JSON into the `data/` folder.
Example expected path:

```bash
./data/Abbie917_Ali918_Heathcote539_42424eb3-41c0-6ce9-bb61-8cbe23935ed4.json
```

## 2) Start Postgres + pgAdmin

```bash
docker compose up -d
```

Services:
- Postgres: `localhost:5432`
- pgAdmin: `http://localhost:5050`

## 3) Load the FHIR bundle

```bash
docker compose --profile loader run --rm fhir_loader
```

## 4) Connect from pgAdmin
Register a new server with:
- Host: `postgres`
- Port: `5432`
- Database: value of `POSTGRES_DB`
- Username: value of `POSTGRES_USER`
- Password: value of `POSTGRES_PASSWORD`

If you connect from a desktop SQL client instead of pgAdmin, use `localhost` as the host.

## 5) Useful queries

```sql
select count(*) from fhir.resource_raw;
select * from fhir.patient;

select patient_id, count(*) as encounters
from fhir.encounter
group by patient_id
order by encounters desc;

select patient_id, code_display, value_num, value_unit, effective_time
from fhir.observation
order by effective_time desc
limit 20;

select claim_id, total_value, provider_display
from fhir.claim
order by created_time desc
limit 20;
```

## Reset everything

```bash
docker compose down -v
```

Then start again with:

```bash
docker compose up -d
```

## Notes
- The SQL init scripts run automatically **only on first database initialization**. If you change the schema later, either apply it manually or reset with `docker compose down -v`.
- The loader preserves the original FHIR resources in `fhir.resource_raw.resource_json` and also populates query-friendly relational tables.
- This dataset may contain sensitive identifiers; do not expose this stack publicly without hardening credentials and access.
