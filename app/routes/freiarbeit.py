from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.forms import FreiarbeitEintragForm
from app.models import Person, Lernfeld, FreiarbeitEintrag, ThemaZuweisung
from app.utils import berechne_arbeitsphase
from datetime import date, datetime, timedelta
from sqlalchemy import or_, and_

bp = Blueprint("freiarbeit", __name__, url_prefix="/freiarbeit")


@bp.route("/neu/<int:lernfeld_id>", methods=["GET", "POST"])
def neuer_eintrag(lernfeld_id):
    form = FreiarbeitEintragForm()

    # Datum & Phase vorausfüllen
    if not form.datum.data:
        form.datum.data = date.today()
    if not form.phase.data:
        form.phase.data = berechne_arbeitsphase()

    lernfelder = Lernfeld.query.order_by(Lernfeld.name).all()
    if not lernfelder:
        flash("Es wurden noch keine Lernfelder angelegt.", "warning")
        return redirect(url_for("index"))

    # Person ermitteln
    person_id = request.form.get("person_id") or request.args.get("person_id")
    person = Person.query.get(person_id) if person_id else None
    person_anzeige = (
        f"{person.name_mit_spitzname} – {person.lerngruppe_obj.name if person.lerngruppe_obj else ""}"
        if person else ""
    )

    # Bei GET und ausgewählter Person Thema & Bemerkung vorbefüllen
    bemerkung = ""
    if request.method == "GET" and person:
        zuweisung = ThemaZuweisung.query.filter_by(
            person_id=person.id, lernfeld_id=lernfeld_id
        ).first()
        form.thema_text.data = zuweisung.thema_basistext if zuweisung else ""
        bemerkung = zuweisung.bemerkung if zuweisung else ""

    # Speichern
    if form.validate_on_submit():
        if not person:
            flash("Bitte eine Person auswählen.", "danger")
            return redirect(url_for("freiarbeit.neuer_eintrag", lernfeld_id=lernfeld_id))

        eintrag = FreiarbeitEintrag(
            person_id=person.id,
            datum=form.datum.data,
            phase=form.phase.data,
            lernfeld_id=lernfeld_id,
            thema_text=form.thema_text.data,
            notiz=form.notiz.data
        )
        db.session.add(eintrag)
        db.session.commit()
        flash("Eintrag gespeichert.", "success")
        # zurück ohne person_id, damit das Formular leer ist
        return redirect(url_for("freiarbeit.neuer_eintrag", lernfeld_id=lernfeld_id))

    # ─── Neu: Letzte 40 Einträge heute für dieses Lernfeld ───
    heute = date.today()
    start = datetime(heute.year, heute.month, heute.day)
    ende  = start + timedelta(days=1)
    recent_entries = (
        FreiarbeitEintrag.query
        .filter(
            FreiarbeitEintrag.lernfeld_id == lernfeld_id,
            FreiarbeitEintrag.gespeichert_am >= start,
            FreiarbeitEintrag.gespeichert_am < ende
        )
        .order_by(FreiarbeitEintrag.gespeichert_am.desc())
        .limit(40)
        .all()
    )

    return render_template(
        "freiarbeit/formular.html",
        form=form,
        lernfelder=lernfelder,
        lernfeld_id=lernfeld_id,
        person=person,
        person_anzeige=person_anzeige,
        bemerkung=bemerkung,
        recent_entries=recent_entries
    )

@bp.route("/api/personensuche")
def api_personensuche():
    q = request.args.get("q", "").strip().lower()
    terms = q.split()
    query = Person.query
    if terms:
        filters = [
            or_(
              Person.vorname.ilike(f"%{t}%"),
              Person.nachname.ilike(f"%{t}%"),
              Person.spitzname.ilike(f"%{t}%"),
            )
            for t in terms
        ]
        query = query.filter(and_(*filters))
    personen = query.order_by(Person.vorname, Person.nachname).limit(20).all()

    return jsonify([
        {
            "id": p.id,
            "anzeige": p.name_mit_spitzname + " – " + (p.lerngruppe_obj.name if p.lerngruppe_obj else "")
        }
        for p in personen
    ])


@bp.route("/api/personen")
def api_personen():
    term = request.args.get("q", "").lower()
    ergebnisse = Person.query.filter(
        (Person.vorname.ilike(f"%{term}%")) |
        (Person.nachname.ilike(f"%{term}%")) |
        (Person.spitzname.ilike(f"%{term}%"))
    ).order_by(Person.vorname).limit(20).all()

    return jsonify([
        {
            "id": p.id,
            "text": (
                f"{p.vorname} ({p.spitzname}) {p.nachname} – {(p.lerngruppe_obj.name if p.lerngruppe_obj else '')}"
                if p.spitzname
                else f"{p.vorname} {p.nachname} – {(p.lerngruppe_obj.name if p.lerngruppe_obj else '')}"
            )
        }
        for p in ergebnisse
    ])


@bp.route("/api/thema_vorschlag")
def api_thema_vorschlag():
    person_id = request.args.get("person_id", type=int)
    lernfeld_id = request.args.get("lernfeld_id", type=int)

    if not person_id or not lernfeld_id:
        return jsonify({"thema": ""})

    zuweisung = ThemaZuweisung.query.filter_by(
        person_id=person_id,
        lernfeld_id=lernfeld_id
    ).first()

    return jsonify({"thema": zuweisung.thema_basistext if zuweisung else ""})

@bp.route("/api_thema")
def api_thema():
    pid = request.args.get("person_id", type=int)
    lf  = request.args.get("lernfeld_id", type=int)
    z   = ThemaZuweisung.query.filter_by(
              person_id=pid,
              lernfeld_id=lf
          ).first()
    return jsonify({
        "thema_basistext": z.thema_basistext if z else "",
        "bemerkung":       z.bemerkung        if z else ""
    })



@bp.route("/zuweisung/<int:lernfeld_id>", methods=["GET", "POST"])
def zuweisung_bearbeiten(lernfeld_id):
    person_id = request.args.get("person_id")
    person = Person.query.get(person_id)
    if not person:
        flash("Ungültige Auswahl.", "danger")
        return redirect(url_for("freiarbeit.neuer_eintrag", lernfeld_id=lernfeld_id))

    zuweisung = ThemaZuweisung.query.filter_by(
        person_id=person.id,
        lernfeld_id=lernfeld_id
    ).first()

    if request.method == "POST":
        thema = request.form.get("thema_basistext", "").strip()
        bemerkung = request.form.get("bemerkung", "").strip()
        if zuweisung:
            zuweisung.thema_basistext = thema
            zuweisung.bemerkung = bemerkung
        else:
            zuweisung = ThemaZuweisung(
                person_id=person.id,
                lernfeld_id=lernfeld_id,
                thema_basistext=thema,
                bemerkung=bemerkung
            )
            db.session.add(zuweisung)
        db.session.commit()
        flash("Themenzuweisung gespeichert.", "success")
        return redirect(url_for("freiarbeit.neuer_eintrag", lernfeld_id=lernfeld_id, person_id=person.id))


    return render_template(
        "freiarbeit/zuweisung.html",
        lernfeld_id=lernfeld_id,
        person=person,
        zuweisung=zuweisung
    )
