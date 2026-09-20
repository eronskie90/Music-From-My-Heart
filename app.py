from flask import Flask, render_template, request, redirect, jsonify, session
import json
import os
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "music-from-my-heart-development-key"
)

PHOTO_FOLDER = "static/photos"
SETTINGS_FILE = "settings.json"
ENTRIES_FILE = "entries.json"

app.config["PHOTO_FOLDER"] = PHOTO_FOLDER

os.makedirs(PHOTO_FOLDER, exist_ok=True)


# =========================
# DATA FUNCTIONS
# =========================

def load_entries():
    try:
        with open(ENTRIES_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_entries(entries):
    with open(ENTRIES_FILE, "w", encoding="utf-8") as file:
        json.dump(
            entries,
            file,
            indent=4,
            ensure_ascii=False
        )


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            settings,
            file,
            indent=4
        )


# =========================
# LOCK FUNCTIONS
# =========================

def lock_is_configured():
    settings = load_settings()

    return bool(
        settings.get("pin_hash")
    )


def is_unlocked():
    return session.get("unlocked") is True


# =========================
# LOCK SETUP
# =========================

@app.route("/setup-lock", methods=["GET", "POST"])
def setup_lock():

    if lock_is_configured():

        if not is_unlocked():
            return redirect("/lock")

        return redirect("/")

    if request.method == "POST":

        pin = request.form.get(
            "pin",
            ""
        ).strip()

        confirm_pin = request.form.get(
            "confirm_pin",
            ""
        ).strip()

        if not pin or not confirm_pin:

            return render_template(
                "setup_lock.html",
                error="Please enter your PIN."
            )

        if not pin.isdigit():

            return render_template(
                "setup_lock.html",
                error="PIN must contain numbers only."
            )

        if len(pin) < 4 or len(pin) > 8:

            return render_template(
                "setup_lock.html",
                error="PIN must be 4 to 8 digits."
            )

        if pin != confirm_pin:

            return render_template(
                "setup_lock.html",
                error="PINs do not match."
            )

        settings = {
            "pin_hash": generate_password_hash(pin)
        }

        save_settings(settings)

        session["unlocked"] = True

        return redirect("/")

    return render_template(
        "setup_lock.html"
    )


# =========================
# LOCK SCREEN
# =========================

@app.route("/lock", methods=["GET", "POST"])
def lock():

    if not lock_is_configured():

        return redirect("/setup-lock")

    if request.method == "POST":

        pin = request.form.get(
            "pin",
            ""
        ).strip()

        settings = load_settings()

        if check_password_hash(
            settings.get("pin_hash", ""),
            pin
        ):

            session["unlocked"] = True

            return redirect("/")

        return render_template(
            "lock.html",
            error="Incorrect PIN. Please try again."
        )

    return render_template(
        "lock.html"
    )


# =========================
# MANUAL LOCK
# =========================

@app.route("/lock-now")
def lock_now():

    session["unlocked"] = False

    return redirect("/lock")


# =========================
# HOME
# =========================

@app.route("/")
def home():

    if not lock_is_configured():

        return redirect("/setup-lock")

    if not is_unlocked():

        return redirect("/lock")

    entries = load_entries()

    for index, item in enumerate(entries):

        item["id"] = index

    return render_template(
        "index.html",
        entries=list(enumerate(entries))
    )


# =========================
# WRITE
# =========================

@app.route("/write")
def write():

    if not lock_is_configured():

        return redirect("/setup-lock")

    if not is_unlocked():

        return redirect("/lock")

    return render_template(
        "write.html"
    )


# =========================
# SONG API
# =========================

@app.route("/api/search-song")
def search_song():

    if not lock_is_configured():

        return jsonify([]), 403

    if not is_unlocked():

        return jsonify([]), 403

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify([])

    api_url = (
        "https://itunes.apple.com/search"
        "?term="
        + quote_plus(query)
        + "&media=music"
        + "&entity=song"
        + "&limit=10"
    )

    try:

        api_request = Request(
            api_url,
            headers={
                "User-Agent":
                "MusicFromMyHeart/1.0"
            }
        )

        with urlopen(
            api_request,
            timeout=10
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        songs = []

        for result in data.get(
            "results",
            []
        ):

            track_id = result.get(
                "trackId"
            )

            track_name = result.get(
                "trackName"
            )

            artist_name = result.get(
                "artistName"
            )

            artwork_url = result.get(
                "artworkUrl100"
            )

            preview_url = result.get(
                "previewUrl"
            )

            if not track_id or not track_name:

                continue

            if artwork_url:

                artwork_url = artwork_url.replace(
                    "100x100",
                    "300x300"
                )

            songs.append({

                "track_id":
                    str(track_id),

                "track_name":
                    track_name,

                "artist_name":
                    artist_name or "",

                "artwork_url":
                    artwork_url or "",

                "preview_url":
                    preview_url or ""

            })

        return jsonify(songs)

    except Exception as error:

        print(
            "Song API error:",
            error
        )

        return jsonify([])


# =========================
# SAVE MEMORY
# =========================

@app.route(
    "/save",
    methods=["POST"]
)
def save():

    if not is_unlocked():

        return redirect("/lock")

    title = request.form.get(
        "title",
        ""
    ).strip()

    entry = request.form.get(
        "entry",
        ""
    ).strip()

    entry_date = request.form.get(
        "date",
        ""
    ).strip()

    song_track_id = request.form.get(
        "song_track_id",
        ""
    ).strip()

    song_track_name = request.form.get(
        "song_track_name",
        ""
    ).strip()

    song_artist_name = request.form.get(
        "song_artist_name",
        ""
    ).strip()

    song_artwork_url = request.form.get(
        "song_artwork_url",
        ""
    ).strip()

    song_preview_url = request.form.get(
        "song_preview_url",
        ""
    ).strip()

    song = None

    if (
        song_track_id
        and song_track_name
    ):

        song = {

            "track_id":
                song_track_id,

            "track_name":
                song_track_name,

            "artist_name":
                song_artist_name,

            "artwork_url":
                song_artwork_url,

            "preview_url":
                song_preview_url

        }

    photos = request.files.getlist(
        "photos"
    )

    photo_filenames = []

    for photo in photos:

        if photo and photo.filename:

            photo_filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    app.config["PHOTO_FOLDER"],
                    photo_filename
                )
            )

            photo_filenames.append(
                photo_filename
            )

    new_entry = {

        "title":
            title,

        "date":
            entry_date,

        "entry":
            entry,

        "song":
            song,

        "photos":
            photo_filenames

    }

    entries = load_entries()

    entries.append(
        new_entry
    )

    save_entries(
        entries
    )

    return redirect("/")


# =========================
# EDIT
# =========================

@app.route(
    "/edit/<int:index>"
)
def edit(index):

    if not is_unlocked():

        return redirect("/lock")

    entries = load_entries()

    if (
        index < 0
        or index >= len(entries)
    ):

        return redirect("/")

    return render_template(
        "edit.html",
        item=entries[index],
        index=index
    )


# =========================
# UPDATE
# =========================

@app.route(
    "/update/<int:index>",
    methods=["POST"]
)
def update(index):

    if not is_unlocked():

        return redirect("/lock")

    entries = load_entries()

    if (
        index < 0
        or index >= len(entries)
    ):

        return redirect("/")

    title = request.form.get(
        "title",
        ""
    ).strip()

    entry = request.form.get(
        "entry",
        ""
    ).strip()

    entry_date = request.form.get(
        "date",
        ""
    ).strip()

    old_song = entries[index].get(
        "song"
    )

    old_photos = entries[index].get(
        "photos",
        []
    )

    song_action = request.form.get(
        "song_action",
        ""
    ).strip()

    if song_action == "clear":

        song = None

    else:

        song_track_id = request.form.get(
            "song_track_id",
            ""
        ).strip()

        song_track_name = request.form.get(
            "song_track_name",
            ""
        ).strip()

        song_artist_name = request.form.get(
            "song_artist_name",
            ""
        ).strip()

        song_artwork_url = request.form.get(
            "song_artwork_url",
            ""
        ).strip()

        song_preview_url = request.form.get(
            "song_preview_url",
            ""
        ).strip()

        if (
            song_track_id
            and song_track_name
        ):

            song = {

                "track_id":
                    song_track_id,

                "track_name":
                    song_track_name,

                "artist_name":
                    song_artist_name,

                "artwork_url":
                    song_artwork_url,

                "preview_url":
                    song_preview_url

            }

        else:

            song = old_song

    photos = request.files.getlist(
        "photos"
    )

    photo_filenames = old_photos.copy()

    for photo in photos:

        if photo and photo.filename:

            photo_filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    app.config["PHOTO_FOLDER"],
                    photo_filename
                )
            )

            photo_filenames.append(
                photo_filename
            )

    entries[index] = {

        "title":
            title,

        "date":
            entry_date,

        "entry":
            entry,

        "song":
            song,

        "photos":
            photo_filenames

    }

    save_entries(
        entries
    )

    return redirect("/")


# =========================
# DELETE
# =========================

@app.route(
    "/delete/<int:index>",
    methods=["POST"]
)
def delete(index):

    if not is_unlocked():

        return redirect("/lock")

    entries = load_entries()

    if (
        index < 0
        or index >= len(entries)
    ):

        return redirect("/")

    entry = entries[index]

    song = entry.get(
        "song"
    )

    photos = entry.get(
        "photos",
        []
    )

    if isinstance(
        song,
        str
    ):

        song_path = os.path.join(
            "static/uploads",
            song
        )

        if os.path.exists(
            song_path
        ):

            os.remove(
                song_path
            )

    for photo in photos:

        photo_path = os.path.join(
            app.config["PHOTO_FOLDER"],
            photo
        )

        if os.path.exists(
            photo_path
        ):

            os.remove(
                photo_path
            )

    entries.pop(index)

    save_entries(
        entries
    )

    return redirect("/")


# =========================
# RUN
# =========================

if __name__ == "__main__":

    app.run(
        debug=True
    )