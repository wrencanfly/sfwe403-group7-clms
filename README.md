# Clinical Laboratory Management System

SFWE 403/503 Fall 2026 — Group 7: Yingwei Song, Jiahao Wang, Qihao Wen and Justin Ulloa.

A runnable classroom MVP for patient intake and specimen collection. Built with Python, Django 5.2, server-rendered HTML/CSS and SQLite. No external API or paid service is required.

## Run locally

Python 3.10 or newer is required.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
# Choose a local demonstration password of at least 12 characters.
export CLMS_DEMO_PASSWORD='your-local-demo-password'
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000. Fixture usernames are `manager`, `collector`, `technician`, `cashier`, `patient`, and `provider`. They use the password chosen above. Seeding is repeatable and does not reset existing passwords or overwrite existing records. Newly created staff accounts must change their temporary password at first login; the new password must differ from the current password. Seed accounts are pre-established demonstration accounts.

```sh
python manage.py test lab
python manage.py check
```

## Implemented intake and collection workflow

1. Manager creates staff accounts. Six roles have server-enforced access. Five failed sign-ins lock the account; only managers can unlock it. Lock notifications are written to the ignored `local-mail/` directory for local inspection.
2. Laboratory staff create and update patient demographics and insurance information. Managers and collectors can archive patients while retaining test history.
3. Staff enter walk-in or telephone requests with patient, physician, insurance and test fields. Results begin pending.
4. Managers maintain reagent lots with test/instrument associations, quantity and expiration dates.
5. Collectors check supplies and collect a sample. An atomic conditional stock update blocks expired, empty and mismatched lots. Duplicate collection does not deduct inventory twice.
6. Collectors issue a Code 128 barcode label once per sample. The application records one label issuance. A browser or printer can still make multiple physical copies of an already-issued label; hardware copy enforcement is outside this prototype.
7. Staff inspect linked patient, order, sample and collection-event history. The laboratory profile is editable by managers.

## Architecture

Browser → Django URL routing and role checks → forms and transactional collection service → Django ORM → SQLite.

- `src/lab/models.py`: patient, order, sample, inventory, account and event records.
- `src/lab/services.py`: collection and barcode issuance invariants.
- `src/lab/views.py`: authenticated workflows and access control.
- `src/lab/templates/` and `static/`: local HTML/CSS, no CDN dependency.
- `src/lab/tests.py`: role, lockout, validation, traceability and duplicate-operation tests.

## Release boundaries and remaining work

This is an MVP implementation for team acceptance review. It is not a clinical deployment. All included patient and provider fixtures are fictional. Patient/provider accounts authenticate but do not yet display results. Instrument text imports, two-stage result validation, result delivery, replenishment orders, scheduled stock alerts, purchasing and reports remain in MVP 2. No real payments, email transport, instrument connections or clinical decisions occur.

The local database is intended for a classroom demonstration, not a concurrent production laboratory. Before production use, configure a persistent secret, production settings, managed database, email delivery, hosting, backups, security review and applicable privacy controls. No regulatory compliance claim is made.

## Planning and evidence

- [Jira project](https://jira.def.engr.arizona.edu/projects/SXFT7)
- [Scrum board](https://jira.def.engr.arizona.edu/secure/RapidBoard.jspa?rapidView=194&view=planning.nodetail)
- [Release plan](docs/planning/Group_7_Release_Plan.docx)
- [Resource estimate](docs/planning/Group_7_Resource_Estimate.docx)
- [MVP 1 verification record](docs/mvp1-verification.md)

The original baseline is 84 story points, split 42/42 between two releases. Story points are estimates and are accepted only after the team's acceptance review. Actual hours and completed sprint velocity must be recorded separately from planning assumptions. Include the Jira key in feature commits and have a teammate review changes before marking the corresponding story Done.
