# Generic Survey API — Spec

## Environment Variables

| Key | Description | Example |
|-----|-------------|---------|
| `ENV` | Runtime environment | `local` / `dev` / `prod` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost:5432/survey_db` |
| `SECRET_KEY` | HMAC secret for JWT signing | `long-random-string` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `OTP_EXPIRE_MINUTES` | OTP code TTL | `10` |

---

## JWT Details

- **Access token**: short-lived JWT (`ACCESS_TOKEN_EXPIRE_MINUTES`). Send in `Authorization: Bearer <token>`.
- **Refresh token**: long-lived JWT, stored server-side as `sha256(token)` in `refresh_tokens` table. Rotate on each use.
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

### User Login
```
POST /auth/login
Body: { "email": "...", "password": "..." }

200: { access_token, refresh_token, token_type: "bearer" }
401: invalid credentials
403: account disabled
```

### User Logout / OTP / Password Recovery / Token Refresh
Same pattern as admin, under `/auth/*`.

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
| POST | `/admin/auth/logout` | Admin JWT | Admin logout, revoke refresh token |
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

### Admin Survey Management
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/admin/surveys` | Admin JWT | Create survey with questions |
| GET | `/admin/surveys` | Admin JWT | List all surveys (filterable by status) |
| GET | `/admin/surveys/{id}` | Admin JWT | Get survey detail |
| PATCH | `/admin/surveys/{id}` | Admin JWT | Update title, description, or status |
| DELETE | `/admin/surveys/{id}` | Admin JWT | Delete survey (cascades) |
| POST | `/admin/surveys/{id}/questions` | Admin JWT | Add question to survey |
| PATCH | `/admin/surveys/{id}/questions/{qid}` | Admin JWT | Update question |
| DELETE | `/admin/surveys/{id}/questions/{qid}` | Admin JWT | Delete question |

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

## Run Commands

```bash
# Copy and fill env
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# Auto-generate migration after model changes
alembic revision --autogenerate -m "describe change"

# Rollback last migration
alembic downgrade -1

# Run tests
pytest
```

---

## Data Models

### Survey Lifecycle
```
draft → published → closed
```

### Question Types
- `text` — free-text answer
- `single_choice` — pick one option
- `multiple_choice` — pick multiple options
- `rating` — integer score

### Response Lifecycle
```
in_progress → submitted
```

Anonymous responses (`user_id = null`) are supported for published surveys.
