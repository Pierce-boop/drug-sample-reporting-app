# Community Drug Sample Reporting — mobile-friendly prototype

A mobile-friendly Streamlit app for **local testing** of crowdsourced drug sample reporting. It supports optional photographs, intended substance, physical description, tablet/capsule dimensions, adverse or unexpected effects, search, CSV export and administrator review.

## Start

Install Python 3.10+ and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Or double-click `START_WINDOWS.bat` on Windows (Python must be installed).

On a phone on the **same trusted Wi-Fi network**, open the network URL shown by Streamlit on your computer. Do not expose this development server to the public internet.

## Important limitations

- This is a **local demonstration**, not a production public service or a native iOS/Android app.
- Submissions and images are stored on the computer running Streamlit in `data/` (SQLite and uploads). No cloud database is configured.
- There is **no authentication or user access control**. The review screen is visible to everyone who can access the app; it is for local testing only.
- Only reviewed/approved entries are shown in the public-style browse tab, but this is **not** a security boundary.
- Do not collect personal identifiers or publish sensitive location data. Do not use real sensitive submissions until appropriate privacy/security and moderation controls are built.
- Photos, appearance and self-reports **cannot identify or verify drug composition**. No supplier or transaction details are collected.
- For production: add authenticated moderation, abuse prevention, privacy policy, retention controls, secure object storage, encryption, security review and appropriate clinical/public health governance.
