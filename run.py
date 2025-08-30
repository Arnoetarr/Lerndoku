from app import create_app
from flask import render_template
from app.models import Lernfeld

app = create_app()

@app.route("/")
def index():
    lernfelder = Lernfeld.query.order_by(Lernfeld.name).all()
    return render_template("index.html", lernfelder=lernfelder)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
