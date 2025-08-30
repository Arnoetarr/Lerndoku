from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.models import Person, Lernfeld, LeistungsRueckmeldung
from app.forms import LeistungsRueckmeldungForm
from datetime import date
from sqlalchemy import or_, and_

bp = Blueprint("leistung", __name__, url_prefix="/leistung")

@bp.route("/neu", methods=["GET", "POST"])
def neuer_eintrag():
    # Person ermitteln aus Form/GET
    person_id = request.form.get("person_id") or request.args.get("person_id")
    person = Person.query.get(person_id) if person_id else None
    person_anzeige = (
        f"{person.name_mit_spitzname} – {person.lerngruppe_obj.name if person and person.lerngruppe_obj else ''}"
        if person else ""
    )

    form = LeistungsRueckmeldungForm()
    form.lernfeld.choices = [(lf.id, lf.name) for lf in Lernfeld.query.order_by(Lernfeld.name).all()]
    if not form.datum.data:
        form.datum.data = date.today()

    # Beim Abschicken: speichern und Seite zurücksetzen
    if form.validate_on_submit():
        person = Person.query.get(form.person_id.data)
        if not person:
            flash("Bitte eine Person auswählen.", "danger")
            return redirect(url_for("leistung.neuer_eintrag"))
        eintrag = LeistungsRueckmeldung(
            person_id=person.id,
            lernfeld_id=form.lernfeld.data,
            datum=form.datum.data,
            thema=form.thema.data,
            rueckmeldung=form.rueckmeldung.data,
            note=form.note.data
        )
        db.session.add(eintrag)
        db.session.commit()
        flash("Leistungsrückmeldung gespeichert.", "success")
        # Formular "leeren", bleibt aber auf der Seite!
        return redirect(url_for("leistung.neuer_eintrag"))

    return render_template(
        "leistung/formular.html",
        form=form,
        person=person,
        person_anzeige=person_anzeige
    )

# --- API für Personensuche ---
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
