from . import db
from datetime import datetime


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vorname = db.Column(db.String(100), nullable=False)
    nachname = db.Column(db.String(100), nullable=False)
    spitzname = db.Column(db.String(100))    #Auch Spitznamen, sollen angegeben werden können
    lerngruppe_id = db.Column(db.Integer,db.ForeignKey('lerngruppe.id'), nullable=False)    #z.B. Ameisengeister
    stufe = db.Column(db.Integer, nullable=False)     #aktuelle Klassenstufe, alles von 5 bis 13 ist möglich
    foerderbedarf = db.Column(db.Text)
    foerderbedarf_massnahmen = db.Column(db.Text)  # Notiz zum Förderbedarf, Maßnahmen wie "Taschenrechenr nutzen"
    ziele = db.Column(db.Text)

    freiarbeit_eintraege = db.relationship('FreiarbeitEintrag', backref='person', lazy=True)
    
    @property
    def voller_name(self):
        return f"{self.vorname} {self.nachname}"

    @property
    def name_mit_spitzname(self):
        if self.spitzname:
            return f"{self.vorname} ({self.spitzname}) {self.nachname}"
        return f"{self.vorname} {self.nachname}"
    
class Lernfeld(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class ThemaLLK(db.Model):     #Themen für Lernfelder für die Lernlandkarten
    id = db.Column(db.Integer, primary_key=True)
    thema = db.Column(db.String(100))     #Titel des Themas, Thema nicht zwinged erforderlich
    thema_notiz = db.Column(db.Text)  #Notiz zum Thema (z.B: eigenes Arbeistheft)
    lernfeld_id = db.Column(db.Integer, db.ForeignKey('lernfeld.id'), nullable=False)
    
class ThemaZuweisung(db.Model):  #persönliche Themen der Kinder zu Lernfeldern
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("person.id"), nullable=False)
    lernfeld_id = db.Column(db.Integer, db.ForeignKey("lernfeld.id"), nullable=False)
    thema_basistext = db.Column(db.String(255))  # z. B. "Dezimalbrüche"
    bemerkung = db.Column(db.Text)        # z. B. "hat eigenes Material"

class FreiarbeitEintrag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    datum = db.Column(db.Date, nullable=False)   #Datum, wann die Arbeitsphase war
    phase = db.Column(db.String(50), nullable=False)
    notiz = db.Column(db.Text)
    lernfeld_id = db.Column(db.Integer, db.ForeignKey('lernfeld.id'))
    lernfeld    = db.relationship('Lernfeld', lazy='joined')  # ← neu
    thema_text = db.Column(db.Text)
    gespeichert_am = db.Column(db.DateTime, default=datetime.utcnow)  #Datum wann es gespeichert wurde
    
class Lerngruppe(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    personen = db.relationship('Person', backref='lerngruppe_obj', lazy=True)

class KursRueckmeldung(db.Model):
    __tablename__ = 'kurs_rueckmeldung'
    id             = db.Column(db.Integer, primary_key=True)
    lernfeld_id    = db.Column(db.Integer, db.ForeignKey('lernfeld.id'), nullable=False)
    lerngruppe_id  = db.Column(db.Integer, db.ForeignKey('lerngruppe.id'), nullable=False)
    datum          = db.Column(db.Date, nullable=False)
    phase          = db.Column(db.String(20), nullable=False)
    thema          = db.Column(db.String(255), nullable=False)
    gespeichert_am = db.Column(db.DateTime, default=datetime.utcnow)

    lernfeld   = db.relationship('Lernfeld',   lazy='joined')
    lerngruppe = db.relationship('Lerngruppe', lazy='joined')

    teilnahmen  = db.relationship('KursTeilnahme', backref='rueckmeldung', lazy=True)

class KursTeilnahme(db.Model):
    __tablename__ = 'kurs_teilnahme'
    id          = db.Column(db.Integer, primary_key=True)
    rueckmeldung_id = db.Column(db.Integer, db.ForeignKey('kurs_rueckmeldung.id'), nullable=False)
    person_id   = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    status      = db.Column(db.Enum('anwesend','abwesend', name='status_enum'), nullable=False)
    notiz       = db.Column(db.Text)


class LeistungsRueckmeldung(db.Model):
    __tablename__ = 'leistungs_rueckmeldung'
    id            = db.Column(db.Integer, primary_key=True)
    person_id     = db.Column(db.Integer, db.ForeignKey("person.id"), nullable=False)
    lernfeld_id   = db.Column(db.Integer, db.ForeignKey("lernfeld.id"), nullable=False)
    datum         = db.Column(db.Date, nullable=False)        # Wann wurde erbracht/geprüft
    gespeichert_am= db.Column(db.DateTime, default=datetime.utcnow)
    thema         = db.Column(db.String(255), nullable=False) # Thema oder Anlass
    rueckmeldung  = db.Column(db.Text, nullable=False)        # Kompetenzen/Freitext
    note          = db.Column(db.String(50))                  # Noten/Punkte optional

    lernfeld = db.relationship('Lernfeld', lazy='joined')
    person   = db.relationship('Person', lazy='joined')