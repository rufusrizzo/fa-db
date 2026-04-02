import streamlit as st
from datetime import date
import sqlcipher3
import io
from PIL import Image
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="streamlit")

st.set_page_config(page_title="Firearms Database", layout="wide")
st.title("🔫 Firearms Database")

# ====================== CONFIG ======================
DB_FILE = "firearms_encrypted.db"
PASSWORD = "ChangeThisToAStrongPassword2025!"   # ← CHANGE THIS!

@st.cache_resource(show_spinner=False)
def get_db_connection():
    conn = sqlcipher3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlcipher3.dbapi2.Row
    conn.execute(f"PRAGMA key='{PASSWORD}';")
    conn.execute("PRAGMA cipher_compatibility = 4;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

conn = get_db_connection()
cursor = conn.cursor()

# ====================== CREATE TABLES ======================
cursor.execute('''
CREATE TABLE IF NOT EXISTS firearms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT,
    model TEXT,
    serial TEXT UNIQUE,
    description TEXT,
    type TEXT,
    purpose TEXT,
    special_name TEXT,
    caliber TEXT,
    condition_percent INTEGER CHECK (condition_percent BETWEEN 1 AND 100),
    purchased_from TEXT,
    purchase_price REAL,
    date_purchased DATE,
    catalog_number TEXT,
    stock_grip_type TEXT,
    produced_year INTEGER,
    action TEXT,
    feed_system TEXT,
    sights TEXT,
    optics TEXT,
    optic_zoom_min REAL,
    optic_zoom_max REAL,
    storage_location TEXT,
    is_cr BOOLEAN DEFAULT 0,
    metal_finish TEXT,
    color TEXT,
    place_of_origin TEXT,
    weight_lbs REAL,
    overall_length REAL,
    height REAL,
    barrel_length REAL,
    notes TEXT,
    fired_round_count INTEGER DEFAULT 0,
    sold_date DATE,
    deleted_on DATE,
    created_at DATE DEFAULT CURRENT_DATE,
    status TEXT,
    status_date DATE,
    status_notes TEXT,
    status_party TEXT,
    status_case TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firearm_id INTEGER,
    note_number INTEGER,
    note_text TEXT,
    note_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY(firearm_id) REFERENCES firearms(id) ON DELETE CASCADE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS pictures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firearm_id INTEGER,
    image_blob BLOB,
    filename TEXT,
    display_order INTEGER,
    FOREIGN KEY(firearm_id) REFERENCES firearms(id) ON DELETE CASCADE
)
''')
conn.commit()

COMMON_CALIBERS = [
    "9mm", "45 ACP", "223 Rem", "5.56 NATO", "308 Win", "30-06",
    "12 Gauge", "20 Gauge", "410 Bore", "22 LR", "380 ACP", "40 S&W",
    "357 Mag", "44 Mag", "6.5 Creedmoor", "300 Blackout", "7.62x39",
    "10mm", "Other"
]


# ====================== HELPERS ======================
def safe_int(val):
    """Convert a value to int safely, returning 0 on failure."""
    if val is None:
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def render_firearm_detail(full_row, firearm_id):
    """Render the full detail view for a firearm row. Used in both View All and Search."""
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Make / Model:** {full_row['make'] or ''} {full_row['model'] or ''}")
        st.write(f"**Serial:** {full_row['serial'] or '—'}")
        st.write(f"**Caliber:** {full_row['caliber'] or '—'}")
        st.write(f"**Condition:** {full_row['condition_percent'] if full_row['condition_percent'] is not None else '—'}%")
        st.write(f"**Type:** {full_row['type'] or '—'} | **Purpose:** {full_row['purpose'] or '—'}")
        st.write(f"**Special Name:** {full_row['special_name'] or '—'}")
        st.write(f"**Storage Location:** {full_row['storage_location'] or '—'}")
        st.write(f"**Fired Round Count:** {safe_int(full_row['fired_round_count']):,}")

    with col2:
        price = full_row['purchase_price'] if full_row['purchase_price'] is not None else 0
        st.write(f"**Purchase Price:** ${price:,.2f}")
        st.write(f"**Purchased From:** {full_row['purchased_from'] or '—'}")
        st.write(f"**Date Purchased:** {full_row['date_purchased'] or '—'}")
        st.write(f"**Weight:** {full_row['weight_lbs'] or '—'} lbs")
        st.write(f"**Overall Length:** {full_row['overall_length'] or '—'} in")
        st.write(f"**Barrel Length:** {full_row['barrel_length'] or '—'} in")
        st.write(f"**Optic Zoom:** {full_row['optic_zoom_min'] or '—'}x – {full_row['optic_zoom_max'] or '—'}x")
        st.write(f"**Action:** {full_row['action'] or '—'} | **Feed System:** {full_row['feed_system'] or '—'}")
        st.write(f"**Sights:** {full_row['sights'] or '—'} | **Optics:** {full_row['optics'] or '—'}")
        st.write(f"**Metal Finish:** {full_row['metal_finish'] or '—'} | **Color:** {full_row['color'] or '—'}")
        st.write(f"**Produced Year:** {full_row['produced_year'] or '—'}")
        st.write(f"**Place of Origin:** {full_row['place_of_origin'] or '—'}")
        st.write(f"**C&R Eligible:** {'Yes' if full_row['is_cr'] else 'No'}")
        st.write(f"**Status:** {full_row['status'] or 'Active'}")
        st.write(f"**Status Date:** {full_row['status_date'] or '—'}")
        st.write(f"**Status Notes:** {full_row['status_notes'] or '—'}")
        st.write(f"**Status Party:** {full_row['status_party'] or '—'}")
        st.write(f"**Status Case:** {full_row['status_case'] or '—'}")

    if full_row['description']:
        st.write("**Description:**")
        st.write(full_row['description'])

    if full_row['notes']:
        st.write("**Notes:**")
        st.write(full_row['notes'])

    # Maintenance Notes
    maint = conn.execute("""
        SELECT note_number, note_text, note_date
        FROM maintenance
        WHERE firearm_id = ?
        ORDER BY note_number
    """, (firearm_id,)).fetchall()

    if maint:
        st.write("**Maintenance Notes:**")
        for m in maint:
            st.write(f"• Note {m['note_number']} ({m['note_date']}): {m['note_text']}")

    # Photos
    pics = conn.execute("""
        SELECT image_blob, filename
        FROM pictures
        WHERE firearm_id = ?
        ORDER BY display_order
    """, (firearm_id,)).fetchall()

    if pics:
        st.write("**Photos:**")
        cols = st.columns(min(4, len(pics)))
        for idx, pic in enumerate(pics):
            try:
                img = Image.open(io.BytesIO(pic['image_blob']))
                cols[idx % 4].image(img, caption=pic['filename'], width=250)
            except Exception:
                st.write(f"Could not load image: {pic['filename']}")


def expander_label(row):
    """Build a consistent expander label from a row."""
    status_display = ""
    if row['deleted_on']:
        status_display = "🗑️ DELETED — "
    elif row['sold_date']:
        status_display = "✅ SOLD — "
    elif row['status'] and row['status'] != "Active":
        status_display = f"{row['status']} — "
    return f"{status_display}{row['make'] or '?'} {row['model'] or ''} — {row['serial'] or '(no serial)'}"


# ====================== SIDEBAR ======================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["View All Firearms", "Add New Firearm", "Search"])


# ====================== VIEW ALL FIREARMS ======================
if page == "View All Firearms":
    st.subheader("All Firearms")

    rows = conn.execute("""
        SELECT id, make, model, serial, sold_date, deleted_on, status
        FROM firearms
        ORDER BY
            CASE WHEN deleted_on IS NOT NULL THEN 2
                 WHEN sold_date  IS NOT NULL THEN 1
                 ELSE 0 END,
            date_purchased DESC
    """).fetchall()

    if not rows:
        st.info("No firearms in the database yet.")
    else:
        for row in rows:
            full_row = conn.execute("SELECT * FROM firearms WHERE id = ?", (row['id'],)).fetchone()
            if not full_row:
                continue
            with st.expander(expander_label(row)):
                render_firearm_detail(full_row, row['id'])


# ====================== ADD NEW FIREARM ======================
elif page == "Add New Firearm":
    st.subheader("Add New Firearm")

    with st.form("add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            make = st.text_input("Make *")
            model = st.text_input("Model *")
            serial = st.text_input("Serial Number *")

            caliber_select = st.selectbox("Caliber", COMMON_CALIBERS)
            caliber = caliber_select
            if caliber_select == "Other":
                caliber = st.text_input("Custom Caliber *")

        with col2:
            condition = st.slider("Condition (%)", 1, 100, 85)
            purchase_price = st.number_input("Purchase Price ($)", min_value=0.0, format="%.2f")
            date_purchased = st.date_input("Date Purchased", value=date.today())
            purchased_from = st.text_input("Purchased From")

        with col3:
            ftype = st.text_input("Type")
            purpose = st.text_input("Purpose")
            special_name = st.text_input("Special Name")
            storage_location = st.text_input("Storage Location")

        colA, colB = st.columns(2)
        with colA:
            catalog_number = st.text_input("Catalog #")
            stock_grip = st.text_input("Stock/Grip Type")
            produced_year = st.number_input("Produced Year", 1800, 2026, 2020)
            action = st.text_input("Action")
            feed_system = st.text_input("Feed System")
            sights = st.text_input("Sights")
            optics = st.text_input("Optics")

        with colB:
            optic_zoom_min = st.number_input("Optic Zoom Min (x)", 0.0, step=0.1)
            optic_zoom_max = st.number_input("Optic Zoom Max (x)", 0.0, step=0.1)
            is_cr = st.checkbox("Is C&R")
            metal_finish = st.text_input("Metal Finish")
            color = st.text_input("Color")
            place_of_origin = st.text_input("Place of Origin")
            weight = st.number_input("Weight (lbs)", 0.0, step=0.1)
            overall_length = st.number_input("Overall Length (in)", 0.0, step=0.1)
            height = st.number_input("Height (in)", 0.0, step=0.1)
            barrel_length = st.number_input("Barrel Length (in)", 0.0, step=0.1)

        description = st.text_area("Description")
        notes = st.text_area("General Notes")
        fired_round_count = st.number_input("Fired Round Count", min_value=0, value=0)

        # Status Fields
        status = st.selectbox("Status", ["Active", "Sold", "Deleted", "Stolen", "Transferred", "Consigned"])
        status_date  = None
        status_notes = None
        status_party = None
        status_case  = None

        if status != "Active":
            status_date  = st.date_input("Status Date", value=date.today())
            status_notes = st.text_area("Status Notes")
            if status in ["Sold", "Transferred", "Consigned"]:
                status_party = st.text_input("Party Name")
            if status == "Stolen":
                status_case = st.text_input("Police Case #")

        # Maintenance Notes
        st.subheader("Maintenance Notes (up to 8)")
        maint_notes = []
        for i in range(8):
            note = st.text_input(f"Maintenance Note {i+1}", key=f"maint_note_{i}")
            if note.strip():
                maint_notes.append(note)

        uploaded_files = st.file_uploader(
            "Upload Photos (max 16)", type=["jpg", "jpeg", "png"], accept_multiple_files=True
        )

        if st.form_submit_button("💾 Save Firearm"):
            if not make or not model or not serial or not caliber:
                st.error("Make, Model, Serial, and Caliber are required.")
            else:
                try:
                    cursor.execute('''
                        INSERT INTO firearms
                        (make, model, serial, description, type, purpose, special_name, caliber,
                         condition_percent, purchased_from, purchase_price, date_purchased,
                         catalog_number, stock_grip_type, produced_year, action, feed_system,
                         sights, optics, optic_zoom_min, optic_zoom_max, storage_location,
                         is_cr, metal_finish, color, place_of_origin, weight_lbs,
                         overall_length, height, barrel_length, notes, fired_round_count,
                         sold_date, deleted_on, status, status_date, status_notes, status_party, status_case)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (
                        make, model, serial, description, ftype, purpose, special_name, caliber,
                        condition, purchased_from, purchase_price, date_purchased,
                        catalog_number, stock_grip, produced_year, action, feed_system,
                        sights, optics, optic_zoom_min, optic_zoom_max, storage_location,
                        is_cr, metal_finish, color, place_of_origin, weight,
                        overall_length, height, barrel_length, notes, fired_round_count,
                        status_date if status == "Sold" else None,
                        status_date if status == "Deleted" else None,
                        status,
                        status_date,
                        status_notes,
                        status_party,
                        status_case,
                    ))

                    firearm_id = cursor.lastrowid

                    for idx, note in enumerate(maint_notes):
                        cursor.execute(
                            "INSERT INTO maintenance (firearm_id, note_number, note_text) VALUES (?,?,?)",
                            (firearm_id, idx + 1, note)
                        )

                    for i, file in enumerate(uploaded_files[:16]):
                        cursor.execute(
                            "INSERT INTO pictures (firearm_id, image_blob, filename, display_order) VALUES (?,?,?,?)",
                            (firearm_id, file.getvalue(), file.name, i)
                        )

                    conn.commit()
                    st.success(f"✅ {make} {model} saved successfully!")
                    st.rerun()

                except sqlcipher3.dbapi2.IntegrityError as e:
                    st.error(f"Could not save: {e} (Serial number may already exist.)")


# ====================== SEARCH ======================
elif page == "Search":
    st.subheader("Search Firearms")

    search_field = st.selectbox("Search in", [
        "All Fields", "Make", "Model", "Serial", "Caliber",
        "Special Name", "Storage Location", "Status"
    ])
    search_term = st.text_input("Search term")

    if search_term:
        field_map = {
            "Make": "make", "Model": "model", "Serial": "serial",
            "Caliber": "caliber", "Special Name": "special_name",
            "Storage Location": "storage_location", "Status": "status",
        }

        if search_field == "All Fields":
            query = """
                SELECT id, make, model, serial, sold_date, deleted_on, status
                FROM firearms
                WHERE make LIKE ? OR model LIKE ? OR serial LIKE ?
                   OR caliber LIKE ? OR special_name LIKE ? OR status LIKE ?
            """
            params = (f"%{search_term}%",) * 6
        else:
            col = field_map[search_field]
            query = f"""
                SELECT id, make, model, serial, sold_date, deleted_on, status
                FROM firearms WHERE {col} LIKE ?
            """
            params = (f"%{search_term}%",)

        results = conn.execute(query, params).fetchall()

        if not results:
            st.info("No results found.")
        else:
            st.write(f"{len(results)} result{'s' if len(results) != 1 else ''} found.")
            for row in results:
                full_row = conn.execute(
                    "SELECT * FROM firearms WHERE id = ?", (row['id'],)
                ).fetchone()
                if not full_row:
                    continue
                with st.expander(expander_label(row)):
                    render_firearm_detail(full_row, row['id'])
    else:
        st.info("Enter a search term above.")

st.caption("Encrypted Firearms Database • Streamlit + SQLCipher")
