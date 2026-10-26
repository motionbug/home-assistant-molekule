# Home Assistant compatibility update

Approved by the user on 2026-10-26.

Restore installation and setup on current Home Assistant while retaining the
existing Molekule cloud protocol, Cognito pool/client, request URLs, payloads,
account fields, model capabilities, and entity unique IDs.

Use a focused compatibility patch rather than a rewrite. Check dependency
installation on current Python; replace the obsolete Cognito wrapper only if
needed, keeping its SRP authentication and token interface. Modernize options
flow ownership, correct polling option storage, explicitly bind the coordinator
to its config entry, and clean up clients after failed setup. Fix refresh locking
and retry cleanup without changing command semantics.

Add tests using real Home Assistant classes with mocked network boundaries.
Cover initial setup, errors, options, API request contracts, retry/renewal,
entity IDs, and model behavior. Supply English translations for custom-component
UI strings. Update release metadata and developer/test instructions.

Live HACS installation and real-device verification require the user's instance;
do not claim these from local tests. Exact reported installation cause remains
unconfirmed until a log is provided.
