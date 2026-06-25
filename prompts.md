# prompts.md — notesapp-backend

Log of AI prompts used during Week 2 backend development.

---

## Week 2 — Backend, REST, CRUD & ORM

### PR1: Notes CRUD REST API

**Prompt:**
> Set up a Django + DRF project for a Notes API. Create a Note model with title, body, created_at, updated_at. Add CRUD endpoints: GET /api/notes/, POST /api/notes/, GET /api/notes/<id>/, PUT /api/notes/<id>/, PATCH /api/notes/<id>/, DELETE /api/notes/<id>/. Return 201 on create, 204 on delete, 404 when note is missing. Use APIView not ViewSet.

**What I verified:**
- Checked that `_get_note` returns `None` instead of raising, so early return handles 404 cleanly — no nested if/else.
- Confirmed POST returns 201 and not 200.
- Confirmed DELETE returns 204 with no body.

---

### PR2: ORM Models with User–Note Relationship

**Prompt:**
> Add a ForeignKey from Note to Django's built-in User model. Make it nullable for now since JWT auth comes in Week 3. Generate and apply the migration. Update views to use select_related("user") to avoid N+1 queries. Expose user as a read-only PK field in the serializer.

**What I verified:**
- Reviewed the generated migration `0002_note_user.py` — confirmed it adds the FK with `null=True`.
- Confirmed `select_related("user")` is present in both `NoteListView.get` and `NoteDetailView._get_note`.
- Confirmed `user` is `read_only=True` in the serializer so clients cannot set it manually.

---

### PR3: Input Validation and Status Codes

**Prompt:**
> Add DRF serializer validation to NoteSerializer: title must be non-blank after stripping whitespace. Add a custom DRF exception handler that catches unhandled exceptions, logs them server-side with Python's logging module, and returns a generic JSON 500 response so no stack traces ever reach the client.

**What I verified:**
- Tested that `POST /api/notes/` with `{"body": "x"}` returns 400 with `"title"` key in the error response.
- Confirmed the custom handler is wired in `REST_FRAMEWORK["EXCEPTION_HANDLER"]` in settings.py.
- Checked that `custom_exception_handler` calls `drf_exception_handler` first and only returns the 500 fallback when DRF doesn't handle it.

---

### PR4: Backend Linter Configuration

**Prompt:**
> Configure ruff for this Django project. Use line-length 100, target Python 3.13, enable E/F/W/I rule sets, and exclude migrations from the E501 line-too-long rule since Django auto-generates long lines there. Fix all lint errors in the project.

**What I verified:**
- Ran `ruff check .` — output: "All checks passed!"
- Fixed unused imports in `admin.py` (replaced with actual `Note` registration) and `tests.py`.
- Wrapped the long ForeignKey line in `models.py`.

---

### PR5: AI-Generated Unit Tests — Review & Verify

**Prompt:**
> Write pytest tests for the Notes Django REST API using pytest-django. Cover: Note model __str__, default ordering newest-first, blank body, timestamps on create. Cover views: list 200, list returns all notes, create 201, create without title returns 400, retrieve 200, retrieve missing returns 404, PUT 200, PATCH 200, DELETE 204, delete missing returns 404. Use SQLite in-memory via test_settings.py.

**What I reviewed and corrected:**
- Verified the `note` fixture uses `db` marker (not `django_db`) so it composes cleanly with test functions.
- Confirmed all URL names (`note-list`, `note-detail`) match the names in `notes/urls.py`.
- Confirmed `client` is the built-in pytest-django fixture — no custom setup needed.
- All 14 tests pass: `pytest --tb=short` → 14 passed in 1.16s.
