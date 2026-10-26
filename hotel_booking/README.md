# Hotel Booking Website (Flask + SQLite)

A beginner-friendly hotel booking site: browse rooms, book with dates,
see your bookings, and cancel them. Double-bookings are prevented.

## Run it

```bash
cd hotel_booking
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Files

- `app.py` - all the Python code (routes, database, booking rules)
- `templates/` - HTML pages (`base.html` is the shared layout)
- `static/style.css` - styling
- `hotel.db` - SQLite database, created automatically on first run

## Ideas to extend it

1. Add a room search by dates and guest count
2. Add user login (Flask-Login)
3. Add an admin page to add/edit rooms
4. Add room photos
