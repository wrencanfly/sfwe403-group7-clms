# Clinical Laboratory Management System

SFWE 403/503 Fall 2026 semester project — Group 7.

CLMS manages patient test requests, specimen collection, instrument results, laboratory inventory, purchases and reports. This repository currently contains the project plans and initial folder structure; application implementation has not started here.

## Team

- Yingwei Song
- Jiahao Wang
- Qihao Wen
- Justin Ulloa

## Project planning

- [Jira project SXFT7](https://jira.def.engr.arizona.edu/projects/SXFT7)
- [Group 7 Scrum board](https://jira.def.engr.arizona.edu/secure/RapidBoard.jspa?rapidView=194&view=planning.nodetail)
- [Release plan](docs/planning/Group_7_Release_Plan.docx)
- [Resource estimate](docs/planning/Group_7_Resource_Estimate.docx)

| Release | Planned scope | Story points | Proposed target |
| --- | --- | ---: | --- |
| MVP 1 — Intake and Collection | Accounts, patients, test requests, usable inventory, barcodes and sample history | 42 | November 1, 2026 |
| MVP 2 — Results and Lab Operations | Instrument imports, result validation, replenishment, alerts, purchases, reports and audit review | 42 | November 29, 2026 |

The initial plan estimates 770 total person-hours, including contingency, and 21 accepted story points per two-week sprint. Dates, capacity and the proposed Django/Bootstrap/relational-database stack are planning assumptions to review with the team. See the documents for scope, calculations and acceptance conditions.

## Repository layout

- `src/` — application source, to be implemented.
- `tests/` — automated tests and synthetic fixtures, to be implemented.
- `docs/planning/` — semester resource estimate and release plan.

## Working together

Use a branch named for the Jira story, for example `SXFT7-4-authentication`. Include the Jira key in commits and pull requests. Request teammate review before merging, check the story acceptance conditions, and update Jira through To Do, In Progress, In Review and Done. Record actual work hours separately with Jira Log Work.

Use fictional patient data and simulated payments for development. Keep credentials, local databases, real patient information and unapproved course materials out of Git. The original instructor requirements are supplied through the course and are not redistributed here.

## Running the project

There is no runnable application yet. Add installation, environment configuration, database setup and test commands when the first implementation is merged.
