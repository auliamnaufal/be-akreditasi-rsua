# TRD - RSUA Incident Reporting API

All responses follow `{status_code, message, data}` shape unless an error occurs. Errors return `{error_code, message, details}`. Pagination uses `{items, page, per_page, total}`.

## Auth

### Register User
- **Method:** POST
- **Path:** `/v1/auth/register`
- **Headers:** `Content-Type: application/json`
- **Request:**
```json
{
  "email": "nurse1@rsua.local",
  "full_name": "Perawat UGD",
  "password": "Password123",
  "role": "perawat"
}
```
- **Response 201:**
```json
{
  "status_code": 201,
  "message": "Registered successfully",
  "data": {
    "access_token": "<jwt>",
    "refresh_token": "<jwt>",
    "token_type": "Bearer"
  }
}
```
- **Errors:** 400 `invalid_role`, 409 `email_taken`.

### Login
- **Method:** POST
- **Path:** `/v1/auth/login`
- **Headers:** `Content-Type: application/json`
- **Request:**
```json
{
  "email": "nurse1@rsua.local",
  "password": "Password123"
}
```
- **Response 200:** *(same as register)*
- **Errors:** 401 `invalid_credentials`, 403 `role_not_assigned`.

### Refresh Token
- **Method:** POST
- **Path:** `/v1/auth/refresh`
- **Headers:** `Content-Type: application/json`
- **Request:**
```json
{
  "refresh_token": "<jwt>"
}
```
- **Response 200:** New token pair.
- **Errors:** 401 `invalid_token`, `token_revoked`.

### Logout
- **Method:** POST
- **Path:** `/v1/auth/logout`
- **Headers:** `Authorization: Bearer <access>`
- **Request:** `{}`
- **Response 200:**
```json
{
  "status_code": 200,
  "message": "Logged out",
  "data": {"token_version": 4}
}
```
- **Errors:** 401 `auth_required`.

## Incidents

### Create Draft Incident
- **Method:** POST
- **Path:** `/v1/incidents`
- **Headers:** `Authorization: Bearer <perawat>`
- **Request:**
```json
{
  "patient_identifier": "hash-1234",
  "occurred_at": "2024-02-01T08:30:00Z",
  "location_id": 2,
  "department_id": 5,
  "free_text_description": "Pasien hampir jatuh di kamar mandi",
  "harm_indicator": "NO_HARM",
  "attachments": ["s3://bucket/report1.pdf"]
}
```
- **Response 201:**
```json
{
  "status_code": 201,
  "message": "Incident draft created",
  "data": {
    "id": 101,
    "status": "DRAFT",
    "reporter_id": 12,
    "predicted_category": null,
    "created_at": "2024-02-01T09:00:00Z",
    "updated_at": "2024-02-01T09:00:00Z"
  }
}
```
- **Errors:** 401 `auth_required`, 403 `role_not_allowed`.

### Update Draft Incident
- **Method:** PUT
- **Path:** `/v1/incidents/{id}`
- **Headers:** `Authorization: Bearer <perawat>`
- **Request:**
```json
{
  "free_text_description": "Revisi kronologi kejadian",
  "attachments": ["s3://bucket/report1.pdf", "s3://bucket/foto1.jpg"]
}
```
- **Response 200:** Updated incident snapshot.
- **Errors:** 403 `forbidden`, 409 `invalid_state`.

### Submit Incident (Auto Predict)
- **Method:** POST
- **Path:** `/v1/incidents/{id}/submit`
- **Headers:** `Authorization: Bearer <perawat>`
- **Request:**
```json
{ "confirm_submit": true }
```
- **Response 200:**
```json
{
  "status_code": 200,
  "message": "Incident submitted. Prediction generated.",
  "data": {
    "id": 101,
    "status": "SUBMITTED",
    "predicted_category": "KNC",
    "predicted_confidence": 0.84,
    "model_version": "inc-v1.2.0"
  }
}
```
- **Errors:** 403 `forbidden`, 409 `invalid_state`.

### List Incidents
- **Method:** GET
- **Path:** `/v1/incidents`
- **Headers:** `Authorization: Bearer <token>`
- **Query:** `page`, `per_page`, `status`
- **Response 200:**
```json
{
  "status_code": 200,
  "message": "Incidents fetched",
  "data": {
    "items": [
      {
        "id": 101,
        "status": "SUBMITTED",
        "final_category": null
      }
    ],
    "page": 1,
    "per_page": 20,
    "total": 5
  }
}
```
- **Errors:** 401 `auth_required`.

### Incident Detail
- **Method:** GET
- **Path:** `/v1/incidents/{id}`
- **Headers:** `Authorization`
- **Response 200:** Full incident payload with audit trail.
- **Errors:** 403 `forbidden`, 404 `incident_not_found`.

## Approvals

### PJ Review
- **Method:** POST
- **Path:** `/v1/approvals/{id}/pj`
- **Headers:** `Authorization: Bearer <pj>`
- **Request:**
```json
{
  "category": "KTD",
  "notes": "Pasien mengalami cedera ringan"
}
```
- **Response 200:** Incident with `status = PJ_REVIEWED`, `pj_decision` set.
- **Errors:** 403 `role_not_allowed`, 409 `invalid_state_transition`.

### Mutu Review
- **Method:** POST
- **Path:** `/v1/approvals/{id}/mutu`
- **Headers:** `Authorization: Bearer <mutu>`
- **Request:**
```json
{
  "category": "KTD",
  "notes": "Dikonfirmasi sebagai kejadian tidak diharapkan"
}
```
- **Response 200:** Incident with `status = MUTU_REVIEWED`, `mutu_decision` and `final_category` set.
- **Errors:** 409 `invalid_state_transition` if PJ not complete.

### Close Incident
- **Method:** POST
- **Path:** `/v1/approvals/{id}/close`
- **Headers:** `Authorization: Bearer <mutu/admin>`
- **Request:** `{}`
- **Response 200:** Incident status `CLOSED`.
- **Errors:** 409 `final_category_missing`.

## Admin

### List Users
- **Method:** GET
- **Path:** `/v1/admin/users`
- **Headers:** `Authorization: Bearer <admin>`
- **Response 200:** Array of user objects with roles.
- **Errors:** 403 `role_not_allowed`.

### Create User
- **Method:** POST
- **Path:** `/v1/admin/users`
- **Headers:** `Authorization: Bearer <admin>`
- **Request:**
```json
{
  "email": "mutu2@rsua.local",
  "full_name": "Anggota Mutu",
  "password": "Password123!",
  "role_ids": [3]
}
```
- **Response 201:** Created user.
- **Errors:** 409 `email_taken`.

### Update User
- **Method:** PUT
- **Path:** `/v1/admin/users/{id}`
- **Headers:** `Authorization: Bearer <admin>`
- **Request:**
```json
{
  "full_name": "Koordinator Mutu",
  "password": "NewPassword123!",
  "is_active": true,
  "role_ids": [3]
}
```
- **Response 200:** Updated user record (token_version incremented).
- **Errors:** 404 `user_not_found`.

### Department & Location CRUD
- **Method:** POST/PUT
- **Paths:** `/v1/admin/departments`, `/v1/admin/departments/{id}`, `/v1/admin/locations`, `/v1/admin/locations/{id}`
- **Headers:** `Authorization: Bearer <admin>`
- **Requests:** `{ "name": "Instalasi Gawat Darurat", "description": "UGD" }`
- **Responses:** Standard create/update payloads.

## References

### Incident Categories
- **Method:** GET
- **Path:** `/v1/references/incident-categories`
- **Headers:** None (public)
- **Response 200:**
```json
{
  "status_code": 200,
  "message": "Incident categories",
  "data": [
    {"code": "KTD", "description": "Kejadian Tidak Diharapkan - patient harm occurred."},
    {"code": "KTC", "description": "Kejadian Tidak Cedera - no injury occurred."},
    {"code": "KNC", "description": "Kejadian Nyaris Cedera - near miss."},
    {"code": "KPCS", "description": "Kejadian Potensial Cedera Serius - potential serious injury."},
    {"code": "Sentinel", "description": "Sentinel Event - severe unexpected occurrence."}
  ]
}
```
