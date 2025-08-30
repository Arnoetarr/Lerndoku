from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.models import Person, FreiarbeitEintrag, Lernfeld, Lerngruppe, KursRueckmeldung, KursTeilnahme, LeistungsRueckmeldung
from app.forms import PersonForm
from collections import defaultdict
from datetime import date, timedelta

bp = Blueprint("personen", __name__, url_prefix="/personen")

@bp.route("/", methods=["GET", "POST"])
def liste():
    # Suche per POST → Detail-View
    if request.method == "POST":
        pid = request.form.get("person_id")
        if pid:
            return redirect(url_for("personen.detail", person_id=pid))

    # Personen nach Lerngruppe-Name sortieren
    personen = (
        Person.query
        .join(Lerngruppe)
        .order_by(Lerngruppe.name, Person.vorname, Person.nachname)
        .all()
    )

    # Gruppieren nach Lerngruppe-Name
    gruppiert = defaultdict(list)
    for p in personen:
        gruppiert[p.lerngruppe_obj.name].append(p)

    return render_template(
        "personen/liste.html",
        gruppiert=gruppiert,
        personen=personen
    )

@bp.route("/<int:person_id>", methods=["GET", "POST"])
def detail(person_id):
    person = Person.query.get_or_404(person_id)
    form = PersonForm(obj=person)

    # --- Stammdaten speichern ---
    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(person)
        db.session.commit()
        flash("Stammdaten aktualisiert.", "success")
        return redirect(url_for("personen.detail", person_id=person_id))

    # --- Wochenplan-Tab (unverändert) ---
    alle = (
        FreiarbeitEintrag.query
        .filter_by(person_id=person_id)
        .order_by(FreiarbeitEintrag.datum.desc())
        .all()
    )
    grouped = defaultdict(list)
    for e in alle:
        y, kw, _ = e.datum.isocalendar()
        grouped[(y, kw)].append(e)

    weeks_data = []
    for (y, kw) in sorted(grouped.keys(), reverse=True):
        mo = date.fromisocalendar(y, kw, 1)
        so = date.fromisocalendar(y, kw, 7)
        grid = {
            ap: {dow: {"name": "", "theme": "", "note": ""} for dow in range(1,6)}
            for ap in range(0,7)
        }
        for e in grouped[(y, kw)]:
            ap  = int(e.phase.split(".")[0])
            dow = e.datum.isoweekday()
            if 0 <= ap <= 6 and 1 <= dow <= 5 and e.lernfeld:
                grid[ap][dow] = {
                    "name":  e.lernfeld.name,
                    "theme": e.thema_text.replace('"','\\"'),
                    "note":  (e.notiz or "").replace('"','\\"')
                }
        weeks_data.append({
            "year":   y,
            "week":   kw,
            "monday": mo,
            "sunday": so,
            "grid":   grid
        })

    # --- Eintragungen nach Kalenderwoche ---
    entries = (
        FreiarbeitEintrag.query
        .filter_by(person_id=person_id)
        .order_by(FreiarbeitEintrag.datum.desc())
        .all()
    )
    grouped_entries = defaultdict(list)
    for e in entries:
        y, kw, _ = e.datum.isocalendar()
        grouped_entries[(y, kw)].append(e)

    entry_weeks = []
    for (y, kw) in sorted(grouped_entries.keys(), reverse=True):
        mo = date.fromisocalendar(y, kw, 1)
        fr = mo + timedelta(days=4)
        sorted_entries = sorted(
            grouped_entries[(y, kw)],
            key=lambda e: (e.datum.isoweekday(), int(e.phase.split(".")[0]))
        )
        entry_weeks.append({
            "year":    y,
            "week":    kw,
            "monday":  mo,
            "friday":  fr,
            "entries": sorted_entries
        })

    # --- Eintragungen gruppiert nach Lernfeld ---
    all_entries = (
        FreiarbeitEintrag.query
        .filter_by(person_id=person_id)
        .order_by(FreiarbeitEintrag.datum.desc(), FreiarbeitEintrag.phase)
        .all()
    )
    grouped_by_lf = defaultdict(list)
    for e in all_entries:
        lf_name = e.lernfeld.name if e.lernfeld else "– kein Lernfeld –"
        grouped_by_lf[lf_name].append(e)

    entry_lernfelder = []
    for lf_name, ents in sorted(grouped_by_lf.items(), key=lambda x: x[0].lower()):
        sorted_ents = sorted(
            ents,
            key=lambda e: (e.datum, int(e.phase.split(".")[0])),
            reverse=True
        )
        entry_lernfelder.append({
            "lernfeld": lf_name,
            "entries":  sorted_ents
        })
    teilnahmen = (
        db.session
        .query(KursTeilnahme, KursRueckmeldung)
        .join(KursRueckmeldung, KursTeilnahme.rueckmeldung_id == KursRueckmeldung.id)
        .filter(KursTeilnahme.person_id == person_id)
        .order_by(KursRueckmeldung.datum.desc(), KursRueckmeldung.phase)
        .all()
    )

    rueckmeldungen = LeistungsRueckmeldung.query.filter_by(person_id=person_id).order_by(
        LeistungsRueckmeldung.datum.desc()).all()
    rueckmeldungen_by_lernfeld = defaultdict(list)
    for r in rueckmeldungen:
        lf_name = r.lernfeld.name if r.lernfeld else "-"
        rueckmeldungen_by_lernfeld[lf_name].append(r)

    return render_template(
        "personen/detail.html",
        person=person,
        form=form,
        weeks_data=weeks_data,
        entry_weeks=entry_weeks,
        entry_lernfelder=entry_lernfelder,
        kurs_teilnahmen=teilnahmen,
        rueckmeldungen_by_lernfeld=rueckmeldungen_by_lernfeld
    )


@bp.route("/neu", methods=["GET", "POST"])
def erstellen():
    form = PersonForm()
    # Lerngruppen-Auswahl befüllen
    form.lerngruppe.choices = [
        (g.id, g.name) for g in Lerngruppe.query.order_by(Lerngruppe.name).all()
    ]

    if form.validate_on_submit():
        person = Person(
            vorname        = form.vorname.data,
            nachname       = form.nachname.data,
            spitzname      = form.spitzname.data or None,
            lerngruppe_id  = form.lerngruppe.data,
            stufe          = form.stufe.data,
            foerderbedarf  = form.foerderbedarf.data,
            foerderbedarf_massnahmen = form.foerderbedarf_massnahmen.data,
            ziele          = form.ziele.data
        )
        db.session.add(person)
        db.session.commit()
        flash("Person erfolgreich hinzugefügt.", "success")
        return redirect(url_for("personen.liste"))

    return render_template("personen/erstellen.html", form=form)

@bp.route("/api/suche")
def suche_person():
    q = request.args.get("q", "").lower()
    ergebnisse = (
        Person.query
        .join(Lerngruppe)
        .filter(
            (Person.vorname.ilike(f"%{q}%")) |
            (Person.nachname.ilike(f"%{q}%")) |
            (Person.spitzname.ilike(f"%{q}%"))
        )
        .order_by(Person.vorname, Person.nachname)
        .limit(20)
        .all()
    )
    return jsonify([
        {
            "id": p.id,
            "anzeige": (
                f"{p.vorname}"
                f"{' ('+p.spitzname+')' if p.spitzname else ''} "
                f"{p.nachname} – {p.lerngruppe_obj.name}"
            )
        } for p in ergebnisse
    ])

@bp.route("/import", methods=["GET", "POST"])
def importformular():
    from app.models import Lerngruppe
    if request.method == "POST":
        datei = request.files.get("csv_datei")
        if not datei:
            flash("Keine Datei ausgewählt.", "warning")
            return redirect(request.url)

        import csv, io
        try:
            text = datei.stream.read().decode("utf-8")
        except UnicodeDecodeError:
            text = datei.stream.read().decode("latin-1")

        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(text[:1024])
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        anzahl = 0

        for zeile in reader:
            v = zeile.get("vorname","").strip()
            n = zeile.get("nachname","").strip()
            if not v or not n:
                continue

            grp_name = zeile.get("lerngruppe","").strip()
            gruppe = Lerngruppe.query.filter_by(name=grp_name).first()
            if not gruppe:
                gruppe = Lerngruppe(name=grp_name)
                db.session.add(gruppe)
                db.session.flush()

            person = Person(
                vorname        = v,
                nachname       = n,
                spitzname      = zeile.get("spitzname","").strip() or None,
                lerngruppe_id  = gruppe.id,
                stufe          = int(zeile.get("stufe","0") or 0),
                foerderbedarf  = zeile.get("foerderbedarf","").strip(),
                foerderbedarf_massnahmen = zeile.get("massnahmen","").strip(),
                ziele          = zeile.get("ziele","").strip()
            )
            db.session.add(person)
            anzahl += 1

        db.session.commit()
        flash(f"{anzahl} Personen erfolgreich importiert.", "success")
        return redirect(url_for("personen.liste"))

    return render_template("personen/import.html")

