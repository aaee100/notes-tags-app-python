# Building a Notes and Tags App with Python and Tkinter

## Introduction

Taking notes is useful for recording ideas, organizing information, and keeping track of important details. I built the Notes + Tags App as a lightweight desktop application using Python and Tkinter.

The application allows users to create, edit, search, filter, and delete notes. Each note can contain a title, body text, and multiple tags. Users can also select several notes and export them together into a single text file.

All notes are stored locally in a JSON file. The application does not require an online account, external database, or third-party Python packages.

An important part of this project was improving the reliability of the storage system. During development, the application evolved from a basic note manager into a version that validates its data, creates backups, and uses safer file-saving techniques.

## Features

### 1. Creating and editing notes

Users can create notes by entering a title, writing the note's content, and adding optional tags.

The application requires a title before saving. When an existing note is selected, its information is loaded into the editor, where the user can make changes and save the updated version.

Each note receives a unique identifier generated with Python's `uuid` module. This allows the application to locate the correct note when updating or deleting it, even when several notes have the same title.

### 2. Organizing notes with tags

Users can enter multiple comma-separated tags, such as `Python`, `Projects`, and `Learning`.

The `normalize_tags()` function removes surrounding whitespace, ignores empty entries, and prevents duplicate tags without treating differences in capitalization as separate tags. It preserves the capitalization of the first occurrence.

The application builds a list of all tags currently used by saved notes. Selecting a tag filters the notes list, while the Clear Tag Filter button removes the active filter.

### 3. Searching notes

The search field updates the displayed notes as the user types.

Searches are case-insensitive and check three parts of each note:

- Title
- Body text
- Tags

Search and tag filtering can be used together. This makes it possible to narrow down a large collection without having to browse every note manually.

### 4. Viewing and sorting notes

The main window displays notes in a table with three columns:

- Title
- A short preview of the note
- Last modification timestamp

The preview is generated from the first line of the note body. If that line is longer than the configured limit, it is shortened with an ellipsis.

Notes are sorted by modification timestamp in descending order, so recently edited notes appear first.

### 5. Tracking creation and modification times

Each note stores two timestamps:

- **Created:** when the note was first added.
- **Modified:** when it was last updated.

The application uses the format `YYYY-MM-DD, HH:MM:SS`.

An earlier version stored timestamps in ISO-style formats such as `2025-11-17T16:50:33.774139`. The final version removes the fractional seconds and uses a consistent format instead.

The `fix_timestamp()` function also supports several older timestamp representations. This allows the application to normalize existing records when they are loaded.

### 6. Exporting multiple notes

The notes table supports multiple selection using standard Ctrl and Shift selection.

The Export Selected button opens a file dialog where the user chooses the destination for a single text file containing all selected notes.

Each exported note includes:

- Title
- Creation timestamp
- Modification timestamp
- Tags
- Body text

A separator is placed between notes to make the exported document easier to read.

This feature makes it possible to create a portable text copy of several notes without exporting each one separately.

### 7. Local JSON storage

The application stores notes in `data/notes.json`, relative to the Python script.

The JSON file contains a top-level `notes` list. Each note stores its unique ID, title, body, tags, creation timestamp, and modification timestamp.

The application creates the `data/` directory and an empty JSON file automatically when they do not exist.

It uses UTF-8 encoding and `ensure_ascii=False` when writing JSON, preserving characters from different languages.

## Technologies Used

- **Python:** application logic, data processing, and event handling.
- **Tkinter and ttk:** desktop interface, buttons, editor, notes table, search field, and file dialogs.
- **JSON:** structured local data storage.
- **Pathlib:** project-relative file and directory paths.
- **UUID:** unique identifiers for notes.
- **datetime:** creation and modification timestamps.
- **tempfile, os, and shutil:** temporary files, file replacement, and backups.

## How the Application Works

### 1. Setting up storage

The application locates the folder containing the Python script with `Path(__file__).parent`.

It then creates a `data/` directory and defines paths for:

- `notes.json` — the main notes file.
- `notes.json.bak` — the previous version of the notes file.

The `ensure_data_file()` function creates an initial JSON file containing an empty notes list when necessary.

### 2. Loading and normalizing notes

The `load_notes()` function reads the JSON file and checks that it has the expected structure.

It also handles older data formats:

- Generates IDs for notes that do not have one.
- Converts an older `content` field into `body`.
- Converts string-based tags into lists.
- Normalizes supported creation and modification timestamps.

If normalization changes the records, the application saves the updated data.

Importantly, an unreadable or incorrectly structured file is not treated as an empty collection. Instead, a `NotesFileError` is raised so the application can report the problem without automatically replacing the original file.

### 3. Adding, updating, and deleting notes

The application separates its data operations into reusable functions.

`add_note()` creates a note with a UUID, title, body, tags, and timestamps.

`update_note()` searches for a note by its ID, updates its editable fields, and changes its modification timestamp.

`delete_note()` removes the selected note from the stored collection.

Separating these operations from the GUI makes the program easier to understand and maintain.

### 4. Searching and filtering

The `refresh_notes_list()` method loads the notes, applies the active search query and tag filter, and sorts the matching records by modification time.

The Treeview uses each note's unique ID as its internal item identifier. When a user selects a note, the application can retrieve the corresponding record from the JSON data.

### 5. Safer saving and backups

One of the most important improvements was changing how the application writes the JSON file.

Instead of writing directly over the existing file, `save_notes()` follows several steps:

1. Creates a temporary file in the data directory.
2. Writes the new JSON data to that temporary file.
3. Flushes the data and calls `os.fsync()` to request that it be written to disk.
4. Copies the existing notes file to `notes.json.bak`.
5. Replaces the original file using `os.replace()`.

If an error occurs, the application raises a storage error and attempts to clean up the temporary file.

This approach reduces the risk of losing the previous notes because of an interrupted or unsuccessful save. The backup also provides a previous version that can be used for recovery.

## Development Process and Challenges

The project started with a straightforward task: build a local note-taking application with a graphical interface, JSON storage, search, and tag filtering.

The first version already supported creating and editing notes, but it stored the JSON file in the user's Downloads folder. It also exported only one selected note at a time.

As the application developed, several improvements were requested and implemented.

**Moving beyond single-note export:** The export function was expanded to support multiple selected notes in one text file. The exported information was also extended to include creation and modification timestamps.

**Standardizing timestamps:** Older timestamps used ISO-style formatting, and newly created notes included fractional seconds. The timestamp helper functions were improved to normalize supported formats into `YYYY-MM-DD, HH:MM:SS`.

**Moving storage into the project:** The notes file was moved from Downloads into a project-relative `data/` directory. This made the application easier to organize and distribute as a project.

**Supporting older data:** Existing JSON files could contain older field names, missing IDs, string-based tags, or different timestamp formats. The loading process was improved to normalize these records instead of requiring every file to already use the newest format.

**Preventing accidental data loss:** A particularly important improvement was safer JSON handling. The application was changed to validate the stored data and report problems rather than silently treating a corrupted file as an empty notes list.

**Improving save operations:** Temporary files, backups, and file replacement were introduced to make saving safer. This was an important step in making the application more dependable for everyday use.

## Project Structure

The repository can be organized as follows:

```text
notes-tags-app-python/
├── notes_tags_app.py
├── README.md
├── building-notes-tags-app-python-tkinter-json.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── notes.json
│   └── notes.json.bak
└── screenshots/
    ├── main-window.png
    ├── tags-filter.png
    └── editor-view.png
```

The application creates the `data/` directory and JSON file automatically. Personal notes and their backups should not be committed to a public repository.

For screenshots and examples, use fictional notes rather than personal information.

## Challenges and Lessons Learned

This project provided practical experience with Tkinter, JSON storage, file handling, and event-driven programming.

One important lesson was the value of unique identifiers. A note's title is not necessarily unique, so using UUIDs makes it possible to identify individual records reliably.

Another lesson was that file storage needs more attention than simply opening a file and writing JSON. Existing files can contain older formats, invalid data, or incomplete information. A useful application should detect these situations and avoid overwriting data when it cannot be read safely.

The export and timestamp improvements also demonstrated how small user requests can lead to meaningful changes in application structure.

## Limitations and Future Improvements

The application covers its main note-management functions, but several improvements could make it more convenient:

- Rich text or Markdown support.
- Importing notes from TXT or Markdown files.
- Tag renaming and management.
- Pinned or favorite notes.
- Keyboard shortcuts.
- Improved search with highlighted matches.
- A dedicated backup restoration interface.
- Optional dark mode.
- More detailed validation of individual note fields.

## Conclusion

The Notes + Tags App demonstrates how Python and Tkinter can be used to build a practical desktop application for managing personal information.

It combines note editing, tags, live search, filtering, timestamps, and multi-note export with local JSON storage.

The most valuable development step was improving the reliability of the storage system. Validation, temporary-file saving, and automatic backups make the final application more careful about protecting existing user data.

The project provided useful experience with GUI development, structured data, backward compatibility, and safer file operations, while leaving a clear foundation for future improvements.