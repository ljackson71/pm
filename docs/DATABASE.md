# Database

SQLite via the Python stdlib `sqlite3` module. The file path comes from `DB_PATH` (default `data/app.db`). In Docker, `data/` is a mounted volume, so data survives container restarts.

## Approach

- On startup the backend creates the database file and tables if they do not exist, and inserts the `user` row if missing. No migration tool for the MVP.
- Each user has at most one board. The whole board is stored as a single JSON document in the `BoardData` shape the frontend already uses, and is read and written as a whole (`GET` / `PUT /api/board`). This matches how the AI returns board updates and avoids mapping columns and cards to rows.
- The first time a user's board is requested, it is created from the demo board (5 columns, 8 cards). The backend keeps its own copy of the demo data, matching the frontend's `initialData`.
- Foreign keys are enabled per connection (`PRAGMA foreign_keys = ON`).

## Schema

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS boards (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    data TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

- `boards.user_id` is `UNIQUE`, which enforces one board per user. Multiple users are supported.
- There is no password column. Sign-in is hardcoded for the MVP; a `password_hash` column can be added to `users` when real accounts are needed.
- The session stores the username. Board routes look up the user's id from it.

## Board JSON

`boards.data` holds this shape (validated by Pydantic on `PUT`):

- `columns`: ordered list of `{ id, title, cardIds }`; `cardIds` is the ordered list of cards in that column.
- `cards`: object of `{ id, title, details }` keyed by card id.
- Every id in a column's `cardIds` must exist in `cards`.

Example (trimmed to 2 columns and 3 cards; the seed has 5 columns and 8 cards):

```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"] },
    { "id": "col-done", "title": "Done", "cardIds": ["card-7"] }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics."
    },
    "card-2": {
      "id": "card-2",
      "title": "Gather customer signals",
      "details": "Review support tags, sales notes, and churn feedback."
    },
    "card-7": {
      "id": "card-7",
      "title": "Ship marketing page",
      "details": "Final copy approved and asset pack delivered."
    }
  }
}
```
