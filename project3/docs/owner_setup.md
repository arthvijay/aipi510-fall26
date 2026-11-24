# Owner-only actions

This repository is prepared for Streamlit Community Cloud at
`project3/frontend/streamlit_app.py`, using Python 3.11 and
`project3/frontend/requirements.txt`.
If the authenticated browser is unavailable, sign in at
<https://share.streamlit.io>, select this repository, the `main` branch, and
that entry point, then deploy publicly. No secret is required because the
committed public API configuration is non-sensitive.

The API is deployed publicly at
`https://ridecast-api-oidv2f4u5a-uc.a.run.app` using Cloud Run
`--no-invoker-iam-check`. It can be called by browser users without Cloud
authentication. The private GCS bucket is unchanged.
