# Health Ledger

Your medical records, on your own computer, in one place you can search and
print.

Health Ledger keeps lab results, visit notes, letters, portal exports and DNA
test reports in a single private file, and turns them into a document you can
hand a doctor. It runs entirely on your machine. Nothing is uploaded, there is
no account, and there is no server to sign in to.

> **Not medical advice.** Health Ledger is a filing cabinet, not a doctor. It
> does not diagnose or treat anything and it is not an approved medical
> device. Nothing it shows you is a reason to start, stop or change a
> medication. Talk to your doctor or pharmacist.

## Download

Get the latest version from the
[Releases page](https://github.com/YOUR-USERNAME/health-ledger/releases/latest).

| Your computer | Download | Then |
| --- | --- | --- |
| Mac | `HealthLedger-<version>-macOS-arm64.dmg` | Open it, drag Health Ledger to Applications. First launch: **right-click the app, choose Open**. |
| Windows | `HealthLedger-<version>-windows-x64.zip` | Unzip it, open the folder, run `HealthLedger.exe`. First launch: **More info → Run anyway**. |
| Linux | Run from source | See [INSTALL.md](INSTALL.md). |

Those first-launch steps are needed because the app is not signed with a paid
certificate. [INSTALL.md](INSTALL.md) explains what the warnings mean and what
to do about them.

## The first five minutes

1. Open Health Ledger. It starts a small server on your own machine and opens
   your browser. That browser tab *is* the app.
2. It asks where to keep your records. A folder called **Health Ledger** in
   your home folder is suggested; pick anywhere you like. Everything private
   lives there, and only there.
3. Choose **Start fresh** if this is new, or **Import a database** if you are
   moving from another computer or restoring a backup.
4. Go to **Import** and give it a file — a lab PDF, a visit note, a DNA raw
   data download. It shows you what it found and writes nothing until you
   press **Add to my ledger**.
5. When you have a doctor's appointment, go to **Doctor Docs**, pick the
   specialty, and print or save the document it makes.

To quit: use the Health Ledger icon in your menu bar (Mac) or system tray
(Windows) and choose **Quit**. Closing the browser tab leaves it running.

## What you can put in it

- **Documents from your care** — lab results, visit notes, letters, or a
  patient-portal export, as PDF or plain text. Readings inside them (lab
  values, blood pressure, temperature) are pulled out with their dates.
- **A pharmacogenomic test report** — recognised from its text. Adding it also
  fills in which medications each gene is known to affect.
- **DNA raw data** — the download from 23andMe, AncestryDNA, MyHeritage,
  FamilyTreeDNA or Living DNA, zipped or not. Clinical VCF files are not read
  yet.

A scanned page is a picture with no text in it. Health Ledger keeps it with
your records either way, and marks it as having no searchable text.

Importing the same file twice updates what it stored rather than filing a
second copy.

## Where your records live

In the folder you chose in step 2, and nowhere else. The database, the
original files, generated documents, logs and backups all sit under it.

- Nothing is sent anywhere. The app has no analytics, no crash reporting and
  no update check.
- The server listens on `127.0.0.1` only, so no other machine on your network
  can reach it.
- Back it up like any other folder. Use the **Backup** page, or copy the
  folder to a drive. Nobody can recover it for you.
- Moving to a new computer: copy the folder across, install the app, and on
  the first screen choose **Import a database**.

## Making PDFs

The downloadable app makes its documents through your browser's own print
window: choose **Open printable version**, then **Print → Save as PDF**.

Direct PDF generation needs a graphics library that cannot travel inside a
downloadable app. If you run Health Ledger from source and install that
library, the **Generate PDF** buttons appear on their own.
[INSTALL.md](INSTALL.md) has the details.

## If something goes wrong

- The browser tab did not open: go to `http://127.0.0.1:5001` yourself. If
  that port was busy the app picked the next free one — the menu-bar icon
  shows the address it actually used.
- Mac says the app is damaged or from an unidentified developer: right-click
  the app and choose **Open**, once. See [INSTALL.md](INSTALL.md).
- Something else: [open an issue](https://github.com/YOUR-USERNAME/health-ledger/issues).
  Please do not paste your medical records into it.

## For developers

The code is published so you can read it and check what it does with your
records. Start with [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — how it runs
from source, project structure, the design-system and privacy rules, and the
test suite. [packaging/README.md](packaging/README.md) covers building the
downloadable apps.

## Licence

Source-available, not open source: read it, run it, modify it for yourself.
Redistribution and commercial use need permission. See [LICENSE](LICENSE), and
[SECURITY.md](SECURITY.md) for reporting a vulnerability.
