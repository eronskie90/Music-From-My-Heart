# Music From My Heart

Music From My Heart is a personal digital diary web application built with Python and Flask. It allows users to create private memory entries containing their thoughts, emotions, photos, and songs that are meaningful to the moment.

The project combines a simple diary experience with AI-powered emotion detection, Tagalog-to-English translation, and music search through the iTunes Search API.

## Features

- Create, edit, and delete personal diary entries
- Add photos to diary entries
- Search for songs using the iTunes Search API
- Preview available 30-second song clips
- Attach a selected song to a diary entry
- AI-powered emotion detection
- Tagalog-to-English text translation
- PIN-based application lock
- Responsive web interface
- Local JSON-based entry storage

## AI Features

### Emotion Detection

The application uses:

`j-hartmann/emotion-english-distilroberta-base`

The model analyzes the emotional tone of diary text and identifies an emotion such as:

- Joy
- Sadness
- Anger
- Fear
- Surprise
- Love
- Disgust
- Neutral

### Translation

The application uses:

`Helsinki-NLP/opus-mt-tl-en`

This model translates Tagalog text into English before emotion classification.

This allows the application to work with diary entries written in Tagalog or mixed Tagalog-English text.

## Music Search

Music From My Heart uses the iTunes Search API to search for songs.

Users can search for a song directly inside the diary entry form, preview available tracks, and attach a selected song to their entry.

The application retrieves information such as:

- Song title
- Artist
- Album artwork
- 30-second preview

## Technologies Used

### Backend

- Python
- Flask

### Frontend

- HTML
- CSS
- JavaScript

### AI / Machine Learning

- Hugging Face Transformers
- PyTorch
- MarianMT
- DistilRoBERTa

### API

- iTunes Search API

### Data Storage

- JSON

## Project Structure

```text
Music-From-My-Heart/
│
├── app.py
├── entries.json
├── settings.json
├── requirements.txt
├── .gitignore
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── photos/
│
├── templates/
│   ├── index.html
│   ├── write.html
│   ├── edit.html
│   ├── lock.html
│   └── setup_lock.html
│
└── venv/
