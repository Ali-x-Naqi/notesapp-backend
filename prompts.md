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

---

## Week 3 — Auth, Authorization, API Tests & Integration

### PR1: JWT Authentication

**Prompt:**
> Add JWT authentication to the Django backend using djangorestframework-simplejwt. Create a users app with POST /api/auth/register/ that accepts username, email, password, password_confirm, creates the user with create_user() (hashes the password), and returns access + refresh tokens. Wire simplejwt's TokenObtainPairView to POST /api/auth/token/ and TokenRefreshView to POST /api/auth/token/refresh/. Set DEFAULT_AUTHENTICATION_CLASSES to JWTAuthentication and DEFAULT_PERMISSION_CLASSES to IsAuthenticated. Configure CORS for localhost:3000 using django-cors-headers. Update notes views to require auth and filter notes by request.user.

**What I verified:**
- Checked that `create_user()` is called (not `create()`) — passwords are hashed, never stored plain.
- Confirmed `CorsMiddleware` is placed before `SecurityMiddleware` in MIDDLEWARE (required by django-cors-headers docs).
- Confirmed `RegisterView.permission_classes = [AllowAny]` so unauthenticated users can register.
- Confirmed `SIMPLE_JWT` import of `timedelta` is at the top of settings.py (not mid-file) to pass ruff E402.
- Updated all 10 view tests to use `APIClient().force_authenticate()` since auth is now required — 15/15 passing.

---

### PR2: Role-Based Authorization

**Prompt:**
> Add a UserProfile model with a role field (choices: user/admin) using a OneToOne relationship to Django's User. Use a post_save signal to auto-create a profile for every new user. Create a custom DRF permission class IsOwnerOrAdmin: admin users can access any note, regular users only access their own. Apply this permission to NoteDetailView using check_object_permissions. In NoteListView, return all notes for admin users and only own notes for regular users.

**What I reviewed and corrected:**
- Verified the signal uses `if created:` guard to avoid overwriting profiles on User updates.
- Checked that `check_object_permissions` is called after the 404 check — DRF requires this explicit call in APIView (unlike ViewSets where it's automatic).
- Confirmed 403 is returned (not 404) when a regular user tries to access another user's note — this matches the permission system behavior.
- Ran `makemigrations users` — confirmed migration `0001_initial.py` creates the UserProfile table.

---

### PR3: API Tests (5+ covering auth + CRUD + error paths)

**Prompt:**
> Write pytest tests for the auth and CRUD endpoints. Cover: register returns 201 with tokens, register password mismatch returns 400, login valid credentials returns tokens, login invalid returns 401, unauthenticated notes access returns 401, authenticated user can create note 201, user cannot access another user's note 403, admin can access any note 200, admin sees all notes in list, delete non-existent note 404. Use APIClient with force_authenticate and a separate admin fixture.

**What I reviewed and corrected:**
- Confirmed admin fixture sets `profile.role = UserProfile.ROLE_ADMIN` and saves — the signal creates a `user` role profile by default, so this update is needed.
- Verified all URL names match (`auth-register`, `auth-token`, `note-list`, `note-detail`).
- All 25 tests pass: `pytest --tb=short` → 25 passed in 49.30s (JWT signing is slow in tests; acceptable).

---

### PR4: Integration Test (happy path end-to-end)

**Prompt:**
> Write a single integration test that exercises the full lifecycle: Register a new user, authenticate with the returned JWT access token, Create a note (POST), Read the note (GET), Update it (PATCH), Delete it (DELETE), then confirm deletion returns 404. Use real SQLite in-memory DB — no mocks. All steps in one test function so any regression in any layer surfaces immediately.

**What I reviewed and corrected:**
- Confirmed `client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")` correctly sets the header for all subsequent requests.
- Verified each step asserts the correct status code before moving to the next — the test fails fast and clearly if any step breaks.

---

## Week 4 — Agent Concepts: Skills, Hooks, Memory & Plugins

### PR13: Research Agent with Web-Search Skill

**Prompt:**
> Build a ResearchAgent class using the Groq SDK with a raw tool-use loop (no LangChain). Give it a web_search skill backed by SerpAPI. The agent should send the user's question to the model, and if the model requests a tool call, execute web_search and feed the result back as a `role: tool` message, looping until the model returns a final answer or a max-iteration limit is hit.

**What I reviewed and corrected:**
- Switched model from `llama-3.3-70b-versatile` to `meta-llama/llama-4-scout-17b-16e-instruct` after hitting a tool-call format bug on the first model.
- Confirmed `MAX_ITERATIONS = 5` prevents an infinite loop if the model keeps requesting tools without ever finishing.
- Verified `web_search` returns error strings (not exceptions) for missing API key / API failure, since the LLM reads the tool result as plain text.

---

### PR14: Agent Memory Layer

**Prompt:**
> Add a SessionMemory class that stores question/answer pairs from the current session. It should expose get_context() to build a system-prompt string summarizing prior Q&A, so the agent can recall facts it already answered earlier in the same session.

**What I reviewed and corrected:**
- Confirmed `get_context()` returns an empty string (not a placeholder) when there are no entries yet, so the agent doesn't inject a useless system message on the first question.
- Verified `agent.run()` only calls `memory.add()` when the model reaches `finish_reason == "stop"` with a non-empty answer — not on every loop iteration.

---

### PR15: Swagger API Documentation

**Prompt:**
> Add drf-spectacular to auto-generate Swagger/OpenAPI docs for the existing DRF views, with a browsable UI at /api/docs/. Annotate views with @extend_schema where the auto-detected schema isn't accurate.

**What I reviewed and corrected:**
- Confirmed `SPECTACULAR_SETTINGS` in `settings.py` doesn't conflict with the existing JWT auth scheme — verified `/api/docs/` renders and lists all notes/auth endpoints correctly.
- Checked `@extend_schema` annotations on views that use Pydantic-first validation, since drf-spectacular can't infer those from the serializer alone.

---

### PR16: Tool-Call Logging Hook

**Prompt:**
> Add a hooks.py with log_pre() and log_post() functions that fire before and after every tool call in the agent's loop. Log timestamp, tool name, input, duration, and output length to a file (agent/tool_calls.log, gitignored).

**What I reviewed and corrected:**
- Confirmed `tool_calls.log` is added to `.gitignore` since it's a runtime artifact, not source.
- Verified `log_post` computes `duration` using `time.monotonic()` (not `time.time()`), since monotonic clocks aren't affected by system clock adjustments.
- Wrote 3 tests in `test_hooks.py` using `tmp_path` so tests don't pollute the real log file.

---

### PR17: File-Read Plugin

**Prompt:**
> Add a file_read skill: a FILE_READ_TOOL definition and file_read(path) function that reads .txt files with Python's open() and .pdf files with the pypdf package, returning the extracted text (or a clear error string for missing files / unsupported extensions / corrupt PDFs). Wire it into the agent's tool list.

**What I reviewed and corrected:**
- Found and fixed a real bug while wiring this in: the agent's dispatch loop was hardcoded to always call `web_search`, ignoring which tool the model actually requested. Replaced it with a `TOOL_FUNCTIONS` dict keyed by `tool_call.function.name` so each tool call routes to the correct function.
- Verified `page.extract_text()` can return `None` for image-only PDF pages, guarded with `or ""` before joining pages so it doesn't crash.
- Mocked `PdfReader` in tests (same pattern as mocking `GoogleSearch` for web_search) instead of shipping a binary PDF fixture.

---

### PR18: Multi-Hop Demo

**Prompt:**
> Write a demo script showing a single agent answering a multi-hop question that requires file_read -> web_search -> memory.add -> answer, with every tool call visible in tool_calls.log.

**What I reviewed and corrected:**
- Designed the prompt sent to the agent to explicitly require reading a file first to discover a topic, then searching the web on that topic, so the multi-hop chain is forced rather than incidental.
- Confirmed `memory.add()` fires automatically inside `agent.run()` — the demo doesn't need to call it directly, it just needs to reach a final `stop` response.
- Split this into its own PR (chained after PR17) instead of bundling with the file-read plugin, per the one-assignment-per-PR rule.
- Test passes in 3.51s — fast enough for CI.
