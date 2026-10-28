"""Local demonstration only; not suitable for public deployment without security work."""
import csv
import io
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
UPLOADS = DATA / "uploads"
DB = DATA / "samples.sqlite3"
DATA.mkdir(exist_ok=True)
UPLOADS.mkdir(exist_ok=True)

st.set_page_config(page_title="Community Drug Sample Reports", page_icon="🔎", layout="wide")
st.markdown("""<style>
.block-container {max-width:1050px; padding-top:1.5rem;}
[data-testid="stForm"] {border-radius:16px;}
</style>""", unsafe_allow_html=True)


def connect():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS samples (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL, intended TEXT,
            sample_type TEXT NOT NULL, shape TEXT, colour TEXT, imprint TEXT,
            score_lines TEXT, packaging TEXT, description TEXT,
            length_mm REAL, width_mm REAL, thickness_mm REAL, weight_mg REAL,
            approx_region TEXT, encountered_date TEXT, effects TEXT,
            severity TEXT, onset TEXT, photo_paths TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', review_note TEXT
        )""")


def all_samples(status=None):
    with connect() as con:
        if status:
            return [dict(x) for x in con.execute("SELECT * FROM samples WHERE status=? ORDER BY created_at DESC", (status,))]
        return [dict(x) for x in con.execute("SELECT * FROM samples ORDER BY created_at DESC")]


def safe_photo(upload):
    if upload is None:
        return None
    if upload.size > 8 * 1024 * 1024:
        raise ValueError("Each image must be under 8 MB")
    try:
        img = Image.open(io.BytesIO(upload.getvalue()))
        img.verify()
        img = Image.open(io.BytesIO(upload.getvalue())).convert("RGB")
        img.thumbnail((1600, 1600))
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("Invalid image file") from exc
    path = UPLOADS / f"{uuid.uuid4().hex}.jpg"
    img.save(path, format="JPEG", quality=85, optimize=True)
    return str(path.relative_to(DATA))


def num(value):
    return float(value) if value is not None and value > 0 else None


def show_sample(r):
    st.markdown(f"**Sample {r['id']}** · {r['sample_type']} · {r['created_at'][:10]}")
    st.write(f"**Intended substance:** {r['intended'] or 'Not provided'}")
    st.write(f"**Appearance:** {', '.join(x for x in [r['shape'], r['colour'], r['imprint']] if x) or 'Not specified'}")
    st.write(f"**Score lines:** {r['score_lines'] or 'Not specified'}")
    st.write(f"**Packaging:** {r['packaging'] or 'Not specified'}")
    st.write(f"**Description:** {r['description'] or 'Not provided'}")
    dimensions = [f"{label}: {r[key]} {unit}" for label, key, unit in [
        ('Length / diameter', 'length_mm', 'mm'), ('Width', 'width_mm', 'mm'),
        ('Thickness', 'thickness_mm', 'mm'), ('Weight', 'weight_mg', 'mg')
    ] if r[key] is not None]
    if dimensions:
        st.write(' · '.join(dimensions))
    st.write(f"**Approximate region:** {r['approx_region'] or 'Not provided'}")
    st.write(f"**Date encountered:** {r['encountered_date'] or 'Not provided'}")
    st.write(f"**Reported effects:** {r['effects'] or 'None reported'}")
    if r['effects']:
        st.write(f"**Severity:** {r['severity'] or 'Not provided'} · **Onset:** {r['onset'] or 'Not provided'}")
    paths = json.loads(r['photo_paths'])
    if paths:
        cols = st.columns(min(3, len(paths)))
        for i, p in enumerate(paths):
            file = DATA / p
            if file.is_file():
                cols[i % len(cols)].image(str(file), use_container_width=True)
    st.caption("Unverified community report. Appearance and self-reported effects do not establish chemical identity or safety.")


init_db()
st.title("🔎 Community Drug Sample Reports")
st.caption("Mobile-friendly crowdsourced reporting prototype · Local testing only")
st.warning("Drug appearance, photographs and user reports cannot confirm identity, purity or safety. This is not a drug-checking laboratory or emergency service. If someone is seriously unwell, seek emergency medical assistance.")
submit_tab, browse_tab, review_tab, about_tab = st.tabs(["📷 Submit sample", "🔍 Browse reports", "🛡️ Review (demo)", "ℹ️ About"])

with submit_tab:
    st.subheader("Submit a sample report")
    st.write("You may report a substance encountered, intended for purchase, or already used. Do not include names, contact details, supplier information or precise locations.")
    with st.form("submit", clear_on_submit=True):
        intended = st.text_input("Intended / believed substance", max_chars=120, placeholder="e.g. MDMA, diazepam, unknown")
        sample_type = st.selectbox("Physical form", ["Tablet / Pill", "Capsule", "Powder / Crystals", "Blotter", "Liquid", "Other"])
        photos = st.file_uploader("Photographs (front, back, or beside a measurement scale)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, help="Maximum 3 photographs, 8 MB each. Avoid faces, personal details or identifiable backgrounds.")
        colour = st.text_input("Colour", max_chars=80)
        imprint = st.text_input("Logo / imprint / markings", max_chars=120)
        packaging = st.text_input("Packaging description (no supplier details)", max_chars=250)
        description = st.text_area("Other appearance details", max_chars=1000)
        shape = score_lines = None
        length = width = thickness = weight = None
        if sample_type in ("Tablet / Pill", "Capsule"):
            st.markdown("#### Optional dimensions")
            if sample_type == "Tablet / Pill":
                shape = st.selectbox("Shape", ["Not specified", "Round", "Oval", "Oblong", "Square", "Other"])
                score_lines = st.selectbox("Score lines", ["Not specified", "None", "One", "Two", "Other"])
            else:
                shape = "Capsule"
            a, b = st.columns(2)
            with a:
                length = st.number_input("Diameter / length (mm)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
                if sample_type == "Tablet / Pill":
                    thickness = st.number_input("Thickness (mm)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            with b:
                width = st.number_input("Width (mm)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
                weight = st.number_input("Weight (mg)", min_value=0.0, max_value=100000.0, value=0.0, step=1.0)
            st.caption("Leave unknown measurements at zero; they will be saved as missing. A photo beside a ruler can help document size but cannot identify a substance.")
        approx_region = st.text_input("Approximate region (optional; no street address)", max_chars=100)
        encountered_date = st.date_input("Date encountered (optional)", value=None)
        st.markdown("#### Adverse or unexpected effects (optional)")
        effects = st.text_area("Describe any unexpected or adverse effects", max_chars=1500)
        severity = st.selectbox("Severity", ["Not specified", "Mild", "Moderate", "Severe"])
        onset = st.text_input("Approximate time to onset", max_chars=100, placeholder="e.g. 45 minutes")
        consent = st.checkbox("I understand this is an unverified report and will not submit personal or supplier-identifying information.")
        submitted = st.form_submit_button("Submit report", type="primary", use_container_width=True)
    if submitted:
        if not consent:
            st.error("Please confirm the submission notice.")
        elif photos and len(photos) > 3:
            st.error("Please upload no more than three photographs.")
        else:
            saved = []
            try:
                for p in photos or []:
                    saved.append(safe_photo(p))
                identifier = uuid.uuid4().hex[:10].upper()
                values = (
                    identifier, datetime.now(timezone.utc).isoformat(), intended.strip(), sample_type,
                    None if shape == "Not specified" else shape, colour.strip(), imprint.strip(),
                    None if score_lines == "Not specified" else score_lines, packaging.strip(), description.strip(),
                    num(length), num(width), num(thickness), num(weight), approx_region.strip(),
                    str(encountered_date) if encountered_date else None, effects.strip(),
                    severity if effects.strip() and severity != "Not specified" else None,
                    onset.strip() if effects.strip() else None, json.dumps(saved), "pending", None
                )
                with connect() as con:
                    con.execute("""INSERT INTO samples (id,created_at,intended,sample_type,shape,colour,imprint,score_lines,
                        packaging,description,length_mm,width_mm,thickness_mm,weight_mg,approx_region,encountered_date,
                        effects,severity,onset,photo_paths,status,review_note)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", values)
                st.success(f"Report {identifier} saved locally, pending review.")
            except (ValueError, OSError, sqlite3.Error) as exc:
                for p in saved:
                    (DATA / p).unlink(missing_ok=True)
                st.error(f"Could not save report: {exc}")

with browse_tab:
    st.subheader("Browse approved reports")
    rows = all_samples("approved")
    query = st.text_input("Search substance, appearance, markings or effects", key="search")
    form_filter = st.selectbox("Filter by form", ["All"] + sorted(set(r['sample_type'] for r in rows)))
    filtered = [r for r in rows if (form_filter == "All" or r['sample_type'] == form_filter) and
                (not query or any(query.casefold() in str(r[k] or '').casefold() for k in
                 ['id','intended','sample_type','shape','colour','imprint','description','effects']))]
    st.metric("Matching approved reports", len(filtered))
    if filtered:
        df = pd.DataFrame([{k:r[k] for k in ['id','created_at','intended','sample_type','shape','colour','imprint','effects','severity','approx_region']} for r in filtered])
        st.dataframe(df, hide_index=True, use_container_width=True)
        st.download_button("Export filtered CSV", df.to_csv(index=False).encode("utf-8"), "approved_reports.csv", "text/csv")
        for r in filtered:
            with st.expander(f"{r['id']} · {r['intended'] or 'Unknown'} · {r['sample_type']}"):
                show_sample(r)
    else:
        st.info("No approved reports match your search yet.")

with review_tab:
    st.subheader("Review queue — local demonstration")
    st.error("This demonstration has NO LOGIN. Anyone with access to this app can review reports. Do not deploy publicly with this tab enabled.")
    pending = all_samples("pending")
    st.write(f"**{len(pending)} pending reports**")
    for r in pending:
        with st.expander(f"{r['id']} · {r['intended'] or 'Unknown'} · {r['sample_type']}"):
            show_sample(r)
            note = st.text_input("Review note (optional)", key=f"note_{r['id']}")
            left, right = st.columns(2)
            if left.button("Approve", key=f"approve_{r['id']}", use_container_width=True):
                with connect() as con:
                    con.execute("UPDATE samples SET status='approved', review_note=? WHERE id=?", (note, r['id']))
                st.rerun()
            if right.button("Reject", key=f"reject_{r['id']}", use_container_width=True):
                with connect() as con:
                    con.execute("UPDATE samples SET status='rejected', review_note=? WHERE id=?", (note, r['id']))
                st.rerun()

with about_tab:
    st.markdown("""### What this prototype does
- Mobile-responsive submission form, with camera/gallery image upload supported by the phone browser.
- Conditional tablet/capsule dimensions and markings.
- Optional adverse-effect reports and approximate region.
- Local SQLite storage, moderator review, searchable approved reports and CSV export.

### What it does **not** do
- No chemical identification from images; no laboratory confirmation or automated public-health alerts.
- No secure public login, production-grade moderation, cloud synchronization or app-store installation.
- No sales, supplier information, precise addresses or transactions.

**Next stage:** authenticated moderators, secure hosted storage, privacy/retention controls, and a PWA or dedicated mobile frontend. Keep all public reports clearly marked as unverified until supported by laboratory testing.
""")
