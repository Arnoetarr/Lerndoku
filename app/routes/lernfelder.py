from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from app.models import Lernfeld
from app.forms import LernfeldForm

bp = Blueprint("lernfelder", __name__, url_prefix="/lernfelder")

@bp.route("/", methods=["GET", "POST"])
def verwalten():
    form = LernfeldForm()
    lernfelder = Lernfeld.query.order_by(Lernfeld.name).all()

    if form.validate_on_submit():
        neues_lernfeld = Lernfeld(name=form.name.data.strip())
        db.session.add(neues_lernfeld)
        db.session.commit()
        flash("Lernfeld erfolgreich angelegt.", "success")
        return redirect(url_for("lernfelder.verwalten"))

    return render_template("lernfelder/verwalten.html", form=form, lernfelder=lernfelder)
