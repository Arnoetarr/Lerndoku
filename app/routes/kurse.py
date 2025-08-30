from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.models import Lerngruppe, Lernfeld, Person, KursRueckmeldung, KursTeilnahme
from app.forms import KursDokumentationForm
from app.utils import berechne_arbeitsphase
from datetime import date

bp = Blueprint("kurse", __name__, url_prefix="/kurse")

@bp.route("/dokumentieren", methods=["GET", "POST"])
def dokumentieren():
    form = KursDokumentationForm()

    # 1) Defaults bei GET
    if request.method == "GET":
        form.datum.data = date.today()
        form.phase.data = berechne_arbeitsphase()

    # 2) Choices füllen
    form.lernfeld.choices   = [(lf.id, lf.name) for lf in Lernfeld.query.order_by(Lernfeld.name)]
    form.lerngruppe.choices = [(lg.id, lg.name) for lg in Lerngruppe.query.order_by(Lerngruppe.name)]

    # 3) Personen-Liste, wenn Gruppe ausgewählt
    personen = []
    if form.lerngruppe.data:
        personen = (
            Person.query
                  .filter_by(lerngruppe_id=form.lerngruppe.data)
                  .order_by(Person.vorname, Person.nachname)
                  .all()
        )

    # 4) Speichern
    if request.method == "POST":
        # Metadaten
        rueck = KursRueckmeldung(
            lernfeld_id   = form.lernfeld.data,
            lerngruppe_id = form.lerngruppe.data,
            datum         = form.datum.data,
            phase         = form.phase.data,
            thema         = form.thema.data
        )
        db.session.add(rueck)
        db.session.flush()  # um rueck.id zu bekommen

        # IDs aus den Checkboxen
        krank_ids      = set(map(int, request.form.getlist("krank")))
        nichtkurs_ids  = set(map(int, request.form.getlist("nicht_im_kurs")))
        alle_ids       = {p.id for p in personen}

        # 4a) Abwesend (krank)
        for pid in krank_ids:
            db.session.add(KursTeilnahme(
                rueckmeldung_id = rueck.id,
                person_id       = pid,
                status          = "abwesend",
                notiz           = "nicht da"
            ))

        # 4b) Anwesend (alle, die nicht krank und nicht im Kurs)
        present_ids = alle_ids - krank_ids - nichtkurs_ids
        for pid in present_ids:
            note = request.form.get(f"notiz_{pid}", "").strip()
            db.session.add(KursTeilnahme(
                rueckmeldung_id = rueck.id,
                person_id       = pid,
                status          = "anwesend",
                notiz           = note
            ))

        # 4c) Kinder in nichtkurs_ids werden übersprungen

        db.session.commit()
        flash("Kurs dokumentiert.", "success")
        return redirect(url_for("kurse.dokumentieren"))

    return render_template(
        "kurse/dokumentieren.html",
        form=form,
        personen=personen
    )

@bp.route("/api/personen")
def api_personen():
    lid = request.args.get("lerngruppe_id", type=int)
    if not lid:
        return jsonify([])
    ps = (
        Person.query
        .filter_by(lerngruppe_id=lid)
        .order_by(Person.vorname, Person.nachname)
        .all()
    )
    return jsonify([{"id": p.id, "text": p.name_mit_spitzname} for p in ps])
