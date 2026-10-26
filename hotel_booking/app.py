from datetime import date, datetime
import sqlite3

from flask import Flask, flash, g, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "change-this-to-something-random"  # needed for flash messages
DATABASE = "hotel.db"


# ---------- Database helpers ----------
def get_db():
    """Open one database connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # lets us use row["name"]
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and add some sample rooms the first time."""
    db = sqlite3.connect(DATABASE)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price_per_night INTEGER NOT NULL,
            capacity INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            guest_name TEXT NOT NULL,
            guest_email TEXT NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            total_price INTEGER NOT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        );
        """
    )
    if db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO rooms (name, description, price_per_night, capacity) VALUES (?, ?, ?, ?)",
            [
                ("Standard Room", "Cozy room with a queen bed and city view.", 2500, 2),
                ("Deluxe Room", "Spacious room with a king bed and balcony.", 4000, 2),
                ("Family Suite", "Two bedrooms, living area and kitchenette.", 6500, 4),
            ],
        )
    db.commit()
    db.close()


def is_available(db, room_id, check_in, check_out):
    """A room is free if no existing booking overlaps the requested dates."""
    clash = db.execute(
        """
        SELECT 1 FROM bookings
        WHERE room_id = ? AND check_in < ? AND check_out > ?
        """,
        (room_id, check_out, check_in),
    ).fetchone()
    return clash is None


# ---------- Pages ----------
@app.route("/")
def index():
    rooms = get_db().execute("SELECT * FROM rooms").fetchall()
    return render_template("index.html", rooms=rooms)


@app.route("/book/<int:room_id>", methods=["GET", "POST"])
def book(room_id):
    db = get_db()
    room = db.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    if room is None:
        flash("Room not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form["guest_name"].strip()
        email = request.form["guest_email"].strip()
        try:
            check_in = datetime.strptime(request.form["check_in"], "%Y-%m-%d").date()
            check_out = datetime.strptime(request.form["check_out"], "%Y-%m-%d").date()
        except ValueError:
            flash("Please choose valid dates.", "error")
            return render_template("book.html", room=room, today=date.today())

        if not name or not email:
            flash("Name and email are required.", "error")
        elif check_in < date.today():
            flash("Check-in cannot be in the past.", "error")
        elif check_out <= check_in:
            flash("Check-out must be after check-in.", "error")
        elif not is_available(db, room_id, str(check_in), str(check_out)):
            flash("Sorry, that room is already booked for those dates.", "error")
        else:
            nights = (check_out - check_in).days
            total = nights * room["price_per_night"]
            db.execute(
                """INSERT INTO bookings
                   (room_id, guest_name, guest_email, check_in, check_out, total_price)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (room_id, name, email, str(check_in), str(check_out), total),
            )
            db.commit()
            flash(f"Booked! {nights} night(s), total ₹{total}.", "success")
            return redirect(url_for("bookings"))

    return render_template("book.html", room=room, today=date.today())


@app.route("/bookings")
def bookings():
    rows = get_db().execute(
        """
        SELECT bookings.*, rooms.name AS room_name
        FROM bookings JOIN rooms ON rooms.id = bookings.room_id
        ORDER BY check_in
        """
    ).fetchall()
    return render_template("bookings.html", bookings=rows)


@app.route("/cancel/<int:booking_id>", methods=["POST"])
def cancel(booking_id):
    db = get_db()
    db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    db.commit()
    flash("Booking cancelled.", "success")
    return redirect(url_for("bookings"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
