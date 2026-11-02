# MVP 1 verification record

Prepared November 1, 2026. Source implementation added in this delivery. It does not establish that development occurred in earlier sprints or that named teammates individually performed particular work.

## Automated checks

`python manage.py test lab` passed all 16 tests. `python manage.py check` reported no issues. `python manage.py makemigrations --check --dry-run` found no model changes missing migrations.

Coverage includes six-role endpoint access, forced first password change, five consecutive login failures and manager notification/recovery, failure-counter reset, one-time stock consumption, expired/empty/mismatched supply rejection, collector-only actions, one-time barcode issuance, patient archival with retained history, required order fields, nonnegative inventory, manager-only staff creation, rejection of password reuse with first-login completion, successful patient and both order-entry routes, rejection of orders for archived patients, and repeatable seeding after multiple tests for one patient.

## Browser verification

The local in-app browser verified collector login, the overview and request pages, rejection of an expired lot, successful collection using a valid lot, inventory changing from 24 to 23, a generated Code 128 label, and the absence of a second label-issuance action after returning to the request. Screenshots are included with the assignment preparation package.

## Acceptance review still required

- A teammate should exercise the complete patient and order forms and review field completeness against the source requirements.
- Run the workflow in a second desktop browser; this is an explicit acceptance condition of SXFT7-11.
- Inspect the local manager lockout notification, staff creation and first-login password-change UI.
- Confirm single label issuance is the intended interpretation of the one-print requirement.
- Compare implementation with the eight MVP 1 Jira stories before moving them to Done. Passing automated checks is not a substitute for team acceptance.

## Known boundaries

SQLite local deployment, file-based email delivery and browser print-to-PDF are demonstration choices. Instrument results and release workflows are not yet implemented. No actual sprint worklogs or historical velocity are inferred from this delivery.
