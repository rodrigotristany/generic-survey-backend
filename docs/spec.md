# Generic Survey API — Spec

## Environment Variables

| Key | Description | Example |
|-----|-------------|---------|
| `ENV` | Runtime environment | `local` / `dev` / `prod` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@db:5432/survey_db` |
| `SECRET_KEY` | HMAC secret for JWT signing | `long-random-string` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `OTP_EXPIRE_MINUTES` | OTP code TTL | `10` |

When running inside Docker Compose use `host=db`. When running locally use `host=localhost:5433` (mapped port).

---

## JWT Details

- **Access token**: short-lived JWT (`ACCESS_TOKEN_EXPIRE_MINUTES`). Send in `Authorization: Bearer <token>`.
- **Refresh token**: long-lived JWT, stored server-side as `sha256(token)` in `refresh_tokens` table. Rotated on each use.
- **Token type claim**: `type: "admin"` or `type: "user"` inside the access token payload.
- **Algorithm**: HS256.

---

## Auth Flows

### Admin Login
```
POST /admin/auth/login
Body: { "email": "...", "password": "..." }

200: { access_token, refresh_token, token_type: "bearer" }
401: invalid credentials
403: account disabled
```

### Admin Logout
```
POST /admin/auth/logout
Authorization: Bearer <access_token>
Body: { "refresh_token": "..." }

200: { "message": "logged out" }
```

### Admin OTP Verify (2FA)
```
POST /admin/auth/otp/verify
Body: { "email": "...", "otp_code": "123456" }

200: { access_token, refresh_token, token_type: "bearer" }
400: invalid or expired OTP
```

### Admin Password Recovery
```
POST /admin/auth/password-recovery/request
Body: { "email": "..." }
200: always (OTP sent if email exists)

POST /admin/auth/password-recovery/confirm
Body: { "email": "...", "otp_code": "123456", "new_password": "..." }
200: { "message": "password updated" }
400: invalid or expired OTP
```

### Admin Token Refresh
```
POST /admin/auth/token/refresh
Body: { "refresh_token": "..." }

200: { access_token, refresh_token }
401: revoked or expired
```

### User Register
```
POST /auth/register
Body: { "email": "...", "password": "...", "full_name": "..." }

201: { id, email, full_name, enabled }
409: email already registered
422: password does not meet strength requirements
```

Password rules: min 8 chars, uppercase, lowercase, digit, symbol.

### User Login / Logout / OTP / Password Recovery / Token Refresh
Same pattern as admin, under `/auth/*`.

### Get Current User
```
GET /auth/me
Authorization: Bearer <access_token>

200: { id, email, full_name, enabled }
```

---

## Endpoints Table

### Health
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Health check |

### Admin Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/admin/auth/login` | None | Admin login |
| POST | `/admin/auth/logout` | Admin JWT | Logout, revoke refresh token |
| POST | `/admin/auth/otp/verify` | None | Verify OTP for 2FA |
| POST | `/admin/auth/password-recovery/request` | None | Request password recovery OTP |
| POST | `/admin/auth/password-recovery/confirm` | None | Confirm OTP + set new password |
| POST | `/admin/auth/token/refresh` | None | Rotate refresh token |

### User Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | None | Register new user |
| POST | `/auth/login` | None | User login |
| POST | `/auth/logout` | User JWT | User logout |
| POST | `/auth/otp/verify` | None | Verify OTP |
| POST | `/auth/password-recovery/request` | None | Request password recovery OTP |
| POST | `/auth/password-recovery/confirm` | None | Confirm OTP + set new password |
| POST | `/auth/token/refresh` | None | Rotate refresh token |
| GET | `/auth/me` | User JWT | Get current user profile |

### Question Library
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/questions` | Admin JWT | List questions (filter: `type`, `search`) |
| POST | `/admin/questions` | Admin JWT | Create standalone question |
| GET | `/admin/questions/{qid}` | Admin JWT | Get question + options |
| PATCH | `/admin/questions/{qid}` | Admin JWT | Update text or type |
| DELETE | `/admin/questions/{qid}` | Admin JWT | Delete (409 if in use by any group) |
| POST | `/admin/questions/{qid}/options` | Admin JWT | Add option |
| PATCH | `/admin/questions/{qid}/options/{oid}` | Admin JWT | Update option |
| DELETE | `/admin/questions/{qid}/options/{oid}` | Admin JWT | Delete option |

### Admin Survey Management
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/admin/surveys` | Admin JWT | Create survey |
| GET | `/admin/surveys` | Admin JWT | List surveys (filter: `status`) |
| GET | `/admin/surveys/{sid}` | Admin JWT | Get full survey hierarchy |
| PATCH | `/admin/surveys/{sid}` | Admin JWT | Update title, description, or status |
| DELETE | `/admin/surveys/{sid}` | Admin JWT | Delete survey (cascades) |
| POST | `/admin/surveys/{sid}/sections` | Admin JWT | Add section |
| PATCH | `/admin/surveys/{sid}/sections/{sec_id}` | Admin JWT | Update section |
| DELETE | `/admin/surveys/{sid}/sections/{sec_id}` | Admin JWT | Delete section (cascades) |
| POST | `/admin/surveys/{sid}/sections/{sec_id}/groups` | Admin JWT | Add group |
| PATCH | `/admin/surveys/{sid}/sections/{sec_id}/groups/{gid}` | Admin JWT | Update group |
| DELETE | `/admin/surveys/{sid}/sections/{sec_id}/groups/{gid}` | Admin JWT | Delete group (cascades) |
| POST | `/admin/surveys/{sid}/sections/{sec_id}/groups/{gid}/questions` | Admin JWT | Flow A — create question + place in group |
| POST | `/admin/surveys/{sid}/sections/{sec_id}/groups/{gid}/questions/link` | Admin JWT | Flow B — link existing question into group |
| PATCH | `/admin/surveys/{sid}/sections/{sec_id}/groups/{gid}/questions/{gqid}` | Admin JWT | Update placement (is_required, order) |
| DELETE | `/admin/surveys/{sid}/sections/{sec_id}/groups/{gid}/questions/{gqid}` | Admin JWT | Remove placement (question stays in library) |

### Public Surveys
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/surveys` | None | List published surveys |
| GET | `/surveys/{slug}` | None | Get published survey by slug |

### Survey Responses
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/responses/surveys/{survey_id}/start` | Optional User JWT | Start a new response |
| POST | `/responses/{response_id}/submit` | Optional User JWT | Submit answers |
| GET | `/responses/{response_id}` | Admin JWT | Get a response |
| GET | `/responses/surveys/{survey_id}` | Admin JWT | List all responses for a survey |

---

## Data Models

### Survey Hierarchy
```
Survey
  └── Section           (broad category, e.g. "Demographics")
        └── SurveyGroup (sub-theme within section)
              └── GroupQuestion  (placement: is_required + order)
                    └── Question (reusable library entry)
                          └── Option
```

### Enums

**SurveyStatus**: `draft` | `published` | `closed`

**QuestionType**: `text` | `single_choice` | `multiple_choice` | `rating` | `date`

**ResponseStatus**: `in_progress` | `submitted`

**AdminRole**: `superadmin` | `staff`

---

### Auth Models

#### TokenResponse
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

#### MessageResponse
```json
{ "message": "string" }
```

#### UserResponse
```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string | null",
  "enabled": true
}
```

---

### Survey Models

#### OptionOut
```json
{
  "id": "uuid",
  "text": "string",
  "order": 0
}
```

#### QuestionOut
```json
{
  "id": "uuid",
  "text": "string",
  "question_type": "text | single_choice | multiple_choice | rating | date",
  "options": [OptionOut]
}
```

#### GroupQuestionOut
```json
{
  "id": "uuid",
  "question_id": "uuid",
  "is_required": true,
  "order": 0,
  "question": QuestionOut
}
```

#### SurveyGroupOut
```json
{
  "id": "uuid",
  "title": "string",
  "order": 0,
  "group_questions": [GroupQuestionOut]
}
```

#### SectionOut
```json
{
  "id": "uuid",
  "title": "string",
  "order": 0,
  "groups": [SurveyGroupOut]
}
```

#### SurveyOut _(full detail, used on GET)_
```json
{
  "id": "uuid",
  "title": "string",
  "slug": "string",
  "description": "string | null",
  "status": "draft | published | closed",
  "created_by": "uuid",
  "sections": [SectionOut]
}
```

#### SurveyListItem _(used on list endpoints)_
```json
{
  "id": "uuid",
  "title": "string",
  "slug": "string",
  "status": "draft | published | closed",
  "question_count": 0
}
```

---

### Request Bodies

#### POST `/admin/surveys`
```json
{
  "title": "string",
  "description": "string | null"
}
```

#### PATCH `/admin/surveys/{sid}`
```json
{
  "title": "string?",
  "description": "string?",
  "status": "draft | published | closed (optional)"
}
```

#### POST `/admin/surveys/{sid}/sections`
```json
{ "title": "string", "order": 0 }
```

#### PATCH `/admin/surveys/{sid}/sections/{sec_id}`
```json
{ "title": "string?", "order": 0 }
```

#### POST `.../groups`
```json
{ "title": "string", "order": 0 }
```

#### PATCH `.../groups/{gid}`
```json
{ "title": "string?", "order": 0 }
```

#### POST `.../groups/{gid}/questions` — Flow A (create + place)
```json
{
  "text": "string",
  "question_type": "text | single_choice | multiple_choice | rating | date",
  "options": [{ "text": "string", "order": 0 }],
  "is_required": true,
  "order": 0
}
```

#### POST `.../groups/{gid}/questions/link` — Flow B (link existing)
```json
{
  "question_id": "uuid",
  "is_required": true,
  "order": 0
}
```

#### PATCH `.../questions/{gqid}` — update placement only
```json
{ "is_required": true, "order": 0 }
```

#### POST `/admin/questions` — create standalone question
```json
{
  "text": "string",
  "question_type": "text | single_choice | multiple_choice | rating | date",
  "options": [{ "text": "string", "order": 0 }]
}
```

#### POST `/admin/questions/{qid}/options`
```json
{ "text": "string", "order": 0 }
```

---

### Response Models

#### AnswerInput _(used in submit body)_
```json
{
  "group_question_id": "uuid",
  "text_value": "string | null",
  "rating_value": 0,
  "date_value": "YYYY-MM-DD | null",
  "selected_option_ids": ["uuid"]
}
```

#### SubmitResponseRequest
```json
{ "answers": [AnswerInput] }
```

#### AnswerOut
```json
{
  "id": "uuid",
  "group_question_id": "uuid",
  "text_value": "string | null",
  "rating_value": "integer | null",
  "date_value": "YYYY-MM-DD | null",
  "selected_option_ids": ["uuid"]
}
```

#### SurveyResponseOut
```json
{
  "id": "uuid",
  "survey_id": "uuid",
  "user_id": "uuid | null",
  "status": "in_progress | submitted",
  "submitted_at": "ISO 8601 datetime | null",
  "answers": [AnswerOut]
}
```

---

### Answer Rules
- A required question (`is_required: true`) must have a non-empty answer
- `date_value` is only valid when `question_type = date`
- `selected_option_ids` is only valid for `single_choice` and `multiple_choice`
- `single_choice` allows at most one entry in `selected_option_ids`

### Question Library
Questions are independent of surveys. The same question can be placed in multiple groups via `GroupQuestion` (the placement record). Deleting a question that is still linked to any group returns `409 Conflict`.

### Survey Lifecycle
```
draft → published → closed
```
Only `published` surveys accept new responses.

### Response Lifecycle
```
in_progress → submitted
```
Anonymous responses (`user_id: null`) are supported.

---

## Run Commands

```bash
# Copy and fill env
cp .env.example .env

# Docker Compose (recommended)
docker compose up --build

# Create first admin user
docker compose exec app python -m scripts.create_admin \
  --email admin@example.com --password MyPass123! --role superadmin

# Run tests (inside container)
docker compose exec app pytest tests/ -v

# Run tests (local, with DB port exposed on 5433)
DATABASE_URL=postgresql+asyncpg://survey_user:survey_pass@localhost:5433/survey_db \
  pytest tests/ -v

# Manual migration commands
alembic upgrade head
alembic revision --autogenerate -m "describe change"
alembic downgrade -1
```

---

## Docker Setup

| Service | Internal host | Exposed port |
|---------|--------------|--------------|
| API | `app:8000` | `localhost:8000` |
| Postgres | `db:5432` | `localhost:5433` |

`docker-compose.override.yml` is applied automatically on `docker compose up` and enables hot-reload with the project directory mounted as a volume. Omit it (or use `-f docker-compose.yml` only) for production-like builds.

The app container runs `alembic upgrade head` automatically before starting.
