Firearm Database (Streamlit + SQLCipher)

A secure, encrypted, cross-platform firearms inventory application built with Streamlit, SQLCipher, and Python.

This application creates an encrypted database of firearms, maintenance logs, and pictures.
It includes a full web interface for adding, editing, searching, and managing your collection.

🔒 Features
Fully encrypted SQLCipher database (firearms_encrypted.db)
Add, edit, and view full firearm records with 40+ fields
Upload pictures and maintenance notes
Automatic created_at timestamps
Status workflow:
Active
Sold
Deleted / Archived
Stolen
Transferred
Consigned
Restore deleted/sold items
View full detail pages with pictures and maintenance
Runs on Windows, Linux, and macOS
📦 Requirements
Python 3.10+
SQLCipher (varies by OS)
pip packages:
streamlit
sqlcipher3
pillow
🛠️ Installation
Linux Installation
1. Install SQLCipher

Ubuntu/Debian:

sudo apt update
sudo apt install sqlcipher libsqlcipher-dev python3-dev

Fedora:

sudo dnf install sqlcipher sqlcipher-devel

Arch:

sudo pacman -S sqlcipher
2. Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install streamlit sqlcipher3 pillow
3. Place the app

Put firearm-db.py in a project folder.

macOS Installation
1. Install Homebrew (if needed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
2. Install SQLCipher
brew install sqlcipher
3. Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install streamlit sqlcipher3 pillow
Windows Installation
1. Install SQLCipher

Download the latest Windows binaries:

https://github.com/sqlcipher/sqlcipher

Extract them somewhere like:

C:\sqlcipher\
2. Install Python dependencies
python -m venv venv
venv\Scripts\activate
pip install streamlit pillow sqlcipher3-binary

If sqlcipher3 fails, use the sqlcipher3-binary wheel instead.

▶️ Running the Application
Linux / macOS
source venv/bin/activate
streamlit run firearm-db.py
Windows
venv\Scripts\activate
streamlit run firearm-db.py

Streamlit will open your default browser automatically.
If not, visit:

http://localhost:8501
🗄️ Database Password

Inside the script:

PASSWORD = "ChangeThisToAStrongPassword2025!"

You MUST change this before storing real data.

🌐 Using the Web Application

When the app loads, you will see:

➕ Add New Firearm

A form with all input fields:

Make, model, serial
Description
Type (Handgun/Rifle/etc.)
Purpose (Range/Home Defense/Carry/etc.)
Special name
Caliber (including “Other Caliber” entry box)
Condition %
Purchased from, price, date purchased
Catalog number
Stock / grip type
Action, feed system, sights, optics & zoom range
Dimensions (weight, barrel length, OAL, height)
Produced year
Metal finish, color
Place of origin
C&R eligible checkbox
Notes
Fired round count
Status (default: Active)
Status metadata (date / notes / party / case – depends on status)

After submitting, the firearm is stored encrypted.

🔍 Viewing Your Firearms

The home page lists all firearms.
Each entry expands to show:

Full details
All pictures
All maintenance notes
🎯 Detail Page

Click a firearm → you get the full detail view, including:

Make/model
Serial
Caliber
Condition
Type & purpose
Special name
Storage location
Fired round count
Purchase info
Dimensions
Optic zoom range
Action & feed system
Metal finish & color
Produced year & origin
C&R eligible
Status & status details
Description and notes
Maintenance notes
Photos
🔧 Status / Actions

Each firearm has buttons:

✏️ Edit
💲 Sold
🔁 Transfer
🤝 Consign
🚨 Stolen
🗑️ Delete
↩️ Restore

Selecting an action opens a confirmation form to enter:

Status Date
Notes
Party Name
Police Case #

These fields differ based on the action.

🛠️ Maintenance Notes

You can add:

Note #
Note text
Date (defaults to today)
📷 Pictures

You can upload multiple images; the app stores them encrypted inside the DB.

🔐 Database Security

The database is:

Fully encrypted using SQLCipher
Locked with a user-configurable key
Uses:
PRAGMA key
WAL mode
Full foreign key support
Secure defaults

Losing your password = losing access forever.

🧩 Future Enhancements (optional)
Export to PDF
Automatic backups
QR code tagging
CSV import/export
📄 License
