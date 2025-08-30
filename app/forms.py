from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SubmitField, DateField, SelectField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, InputRequired
from datetime import date
from wtforms.validators import DataRequired


class PersonForm(FlaskForm):
    vorname = StringField("Vorname", validators=[DataRequired()])
    nachname = StringField("Nachname", validators=[DataRequired()])
    spitzname = StringField("Spitzname")
    lerngruppe = SelectField("Lerngruppe",coerce=int,validators=[DataRequired()])
    stufe = IntegerField("Stufe", validators=[DataRequired()])
    foerderbedarf = TextAreaField("Förderbedarf")
    foerderbedarf_massnahmen = TextAreaField("Fördermaßnahmen")
    ziele = TextAreaField("Lernziele")
    submit = SubmitField("Speichern")
    
class FreiarbeitEintragForm(FlaskForm):
    datum = DateField("Datum", validators=[DataRequired()])
    phase = SelectField("Arbeitsphase", choices=[(f"{i}.AP", f"{i}.AP") for i in range(7)], validators=[DataRequired()])
    thema_text = StringField("Thema", validators=[DataRequired()])
    notiz = TextAreaField("Notiz")
    submit = SubmitField("Eintrag speichern")
    person_id = HiddenField("Personen-ID")

class LernfeldForm(FlaskForm):
    name = StringField("Name des Lernfelds", validators=[InputRequired()])
    submit = SubmitField("Lernfeld speichern")



class KursDokumentationForm(FlaskForm):
    lernfeld   = SelectField("Lernfeld", coerce=int, validators=[InputRequired()])
    lerngruppe = SelectField("Lerngruppe", coerce=int, validators=[InputRequired()])
    datum      = DateField("Datum", default=date.today, validators=[InputRequired()])
    phase      = SelectField("Arbeitsphase", choices=[(f"{i}.AP", f"{i}.AP") for i in range(7)], validators=[InputRequired()])
    thema      = StringField("Thema", validators=[InputRequired()])
    anwesend   = SelectMultipleField("Anwesend", coerce=int)
    abwesend   = SelectMultipleField("Abwesend", coerce=int)
    submit     = SubmitField("Speichern")

class LeistungsRueckmeldungForm(FlaskForm):
    person_id = HiddenField()  # <- hinzufügen
    lernfeld = SelectField("Lernfeld", coerce=int, validators=[DataRequired()])
    datum = DateField("Datum", validators=[DataRequired()])
    thema = StringField("Thema/Anlass", validators=[DataRequired()])
    rueckmeldung = TextAreaField("Kompetenzen/Leistungsrückmeldung", validators=[DataRequired()])
    note = StringField("Note / Punkte")
    submit = SubmitField("Speichern")