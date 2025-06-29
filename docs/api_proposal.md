# RESTful API Proposal

Base URL: `<hostname>/api/v1/`

## Authentication

All endpoints require authentication except Google SSO endpoints.

### Google SSO Authentication
```
POST /auth/google
GET /auth/google/callback
POST /auth/logout
```

---

## Users

### Get Current User Profile
```
GET /users/me
```
**Response (200):**
```json
{
  "id": 123,
  "email_address": "user@example.com",
  "google_id": "google_user_id_123",
  "name": "John Doe",
  "profile_image_url": "https://example.com/profile.jpg",
  "is_active": true
}
```

### Update Current User Profile
```
PATCH /users/me
```
**Request Body:**
```json
{
  "name": "Updated Name",
  "profile_image_url": "https://example.com/new-profile.jpg"
}
```
**Response (200):**
```json
{
  "id": 123,
  "email_address": "user@example.com",
  "google_id": "google_user_id_123",
  "name": "Updated Name",
  "profile_image_url": "https://example.com/new-profile.jpg",
  "is_active": true
}
```

### Get User Workout Statistics
```
GET /users/me/stats?start_date=2024-01-01&end_date=2024-12-31
```
**Query Parameters:**
- `start_date` (optional): ISO date - start date for statistics calculation
- `end_date` (optional): ISO date - end date for statistics calculation

**Response (200):**
```json
{
  "total_workouts": 45,
  "total_exercises_performed": 215,
  "total_sets": 687,
  "total_weight_lifted": 45670.5,
  "workout_frequency": {
    "weekly_average": 3.2,
    "monthly_counts": {
      "2024-01": 12,
      "2024-02": 10,
      "2024-03": 13,
      "2024-04": 10
    }
  },
  "most_performed_exercises": [
    {
      "exercise_id": 1,
      "exercise_name": "Push-ups",
      "count": 42,
      "total_sets": 126,
      "total_volume": 0.0
    },
    {
      "exercise_id": 15,
      "exercise_name": "Squats",
      "count": 38,
      "total_sets": 114,
      "total_volume": 8550.0
    }
  ],
  "body_part_distribution": {
    "chest": 82,
    "legs": 68,
    "back": 55,
    "shoulders": 48,
    "arms": 42,
    "core": 35
  },
  "personal_records": [
    {
      "exercise_id": 15,
      "exercise_name": "Squats",
      "max_weight": 225.0,
      "achieved_date": "2024-03-15",
      "max_volume_single_set": 2700.0
    },
    {
      "exercise_id": 8,
      "exercise_name": "Bench Press",
      "max_weight": 185.0,
      "achieved_date": "2024-04-02",
      "max_volume_single_set": 1850.0
    }
  ],
  "streak_info": {
    "current_streak": 5,
    "longest_streak": 21,
    "last_workout_date": "2024-04-28"
  }
}
```

---

## Exercises

### List Exercises
```
GET /exercises?is_user_created=false&body_part=chest&modality=bodyweight
```
**Query Parameters:**
- `is_user_created` (optional): boolean - filter by user-created vs system exercises
- `body_part` (optional): string - filter by body part
- `modality` (optional): string - filter by exercise modality

**Response (200):**
```json
{
  "exercises": [
    {
      "id": 1,
      "name": "Push-ups",
      "body_part": "chest",
      "modality": "bodyweight",
      "picture_url": "https://example.com/pushups.jpg",
      "created_by_user_id": null,
      "updated_by_user_id": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "is_user_created": false
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### Get Single Exercise
```
GET /exercises/{exercise_id}
```
**Response (200):**
```json
{
  "id": 1,
  "name": "Push-ups",
  "body_part": "chest",
  "modality": "bodyweight",
  "picture_url": "https://example.com/pushups.jpg",
  "created_by_user_id": null,
  "updated_by_user_id": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "is_user_created": false
}
```

### Create Exercise
```
POST /exercises
```
**Request Body:**
```json
{
  "name": "Custom Push-ups",
  "body_part": "chest",
  "modality": "bodyweight",
  "picture_url": "https://example.com/custom-pushups.jpg"
}
```
**Response (201):**
```json
{
  "id": 2,
  "name": "Custom Push-ups",
  "body_part": "chest",
  "modality": "bodyweight",
  "picture_url": "https://example.com/custom-pushups.jpg",
  "created_by_user_id": 123,
  "updated_by_user_id": 123,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "is_user_created": true
}
```

### Update Exercise
```
PATCH /exercises/{exercise_id}
```
**Request Body:**
```json
{
  "name": "Updated Exercise Name",
  "body_part": "shoulders",
  "modality": "dumbbell",
  "picture_url": "https://example.com/updated.jpg"
}
```
**Response (200):** Same as Get Single Exercise

### Delete Exercise
```
DELETE /exercises/{exercise_id}
```
**Response (204):** No content

### Search Exercises
```
GET /exercises/search?q=push&body_part=chest&modality=bodyweight
```
**Query Parameters:**
- `q` (required): string - search term for exercise name
- `is_user_created` (optional): boolean - filter by user-created vs system exercises
- `body_part` (optional): string - filter by body part
- `modality` (optional): string - filter by exercise modality

**Response (200):**
```json
{
  "exercises": [
    {
      "id": 1,
      "name": "Push-ups",
      "body_part": "chest",
      "modality": "bodyweight",
      "picture_url": "https://example.com/pushups.jpg",
      "created_by_user_id": null,
      "updated_by_user_id": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "is_user_created": false
    },
    {
      "id": 42,
      "name": "Diamond Push-ups",
      "body_part": "chest",
      "modality": "bodyweight",
      "picture_url": "https://example.com/diamond-pushups.jpg",
      "created_by_user_id": null,
      "updated_by_user_id": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "is_user_created": false
    }
  ],
  "total": 2,
  "page": 1,
  "per_page": 20
}
```

---

## Workouts

### List Workouts
```
GET /workouts?start_date=2024-01-01&end_date=2024-01-31&finished=true
```
**Query Parameters:**
- `start_date` (optional): ISO date - filter workouts after date
- `end_date` (optional): ISO date - filter workouts before date
- `finished` (optional): boolean - filter by completion status

**Response (200):**
```json
{
  "workouts": [
    {
      "id": 1,
      "finished_at": "2024-01-01T12:00:00Z",
      "created_by_user_id": 123,
      "updated_by_user_id": 123,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z",
      "exercise_executions": [
        {
          "exercise_id": 1,
          "exercise_name": "Push-ups",
          "exercise_order": 1,
          "note_text": "Good form today",
          "created_at": "2024-01-01T10:30:00Z",
          "updated_at": "2024-01-01T11:30:00Z"
        }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### Get Single Workout
```
GET /workouts/{workout_id}
```
**Response (200):**
```json
{
  "id": 1,
  "finished_at": "2024-01-01T12:00:00Z",
  "created_by_user_id": 123,
  "updated_by_user_id": 123,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "exercise_executions": [
    {
      "exercise_id": 1,
      "exercise_name": "Push-ups",
      "exercise_order": 1,
      "note_text": "Good form today",
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-01T11:30:00Z",
      "sets": [
        {
          "id": 1,
          "exercise_id": 1,
          "note_text": "First set was tough",
          "weight": 0.0,
          "clean_reps": 12,
          "forced_reps": 0,
          "created_at": "2024-01-01T10:30:00Z",
          "updated_at": "2024-01-01T10:30:00Z"
        }
      ]
    }
  ]
}
```

### Create Workout
```
POST /workouts
```
**Response (201):**
```json
{
  "id": 1,
  "finished_at": null,
  "created_by_user_id": 123,
  "updated_by_user_id": 123,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "exercise_executions": []
}
```

### Finish Workout
```
PATCH /workouts/{workout_id}/finish
```
**Response (200):**
```json
{
  "id": 1,
  "finished_at": "2024-01-01T12:00:00Z",
  "created_by_user_id": 123,
  "updated_by_user_id": 123,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "exercise_executions": [
    {
      "exercise_id": 1,
      "exercise_name": "Push-ups",
      "exercise_order": 1,
      "note_text": "Good form today",
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-01T11:30:00Z",
      "sets": [
        {
          "id": 1,
          "exercise_id": 1,
          "note_text": "First set was tough",
          "weight": 0.0,
          "clean_reps": 12,
          "forced_reps": 0,
          "created_at": "2024-01-01T10:30:00Z",
          "updated_at": "2024-01-01T10:30:00Z"
        }
      ]
    }
  ]
}
```

### Delete Workout
```
DELETE /workouts/{workout_id}
```
**Response (204):** No content

---

## Exercise Executions (Nested under Workouts)

### Get Exercise Execution
```
GET /workouts/{workout_id}/exercise-executions/{exercise_id}
```
**Response (200):**
```json
{
  "exercise_id": 1,
  "exercise_name": "Push-ups",
  "exercise_order": 1,
  "note_text": "Good form today",
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-01T11:30:00Z",
  "sets": [
    {
      "id": 1,
      "exercise_id": 1,
      "note_text": "First set was tough",
      "weight": 0.0,
      "clean_reps": 12,
      "forced_reps": 0,
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-01T10:30:00Z"
    }
  ]
}
```

### Create/Update Exercise Execution (Full Replace)
```
PUT /workouts/{workout_id}/exercise-executions/{exercise_id}
```
**Request Body:**
```json
{
  "exercise_order": 1,
  "note_text": "Updated exercise notes",
  "sets": [
    {
      "note_text": "First set",
      "weight": 10.0,
      "clean_reps": 8,
      "forced_reps": 0
    },
    {
      "note_text": "Second set",
      "weight": 12.5,
      "clean_reps": 6,
      "forced_reps": 2
    }
  ]
}
```
**Response (200):** Same as Get Exercise Execution

### Remove Exercise from Workout
```
DELETE /workouts/{workout_id}/exercise-executions/{exercise_id}
```
**Response (204):** No content

### Update Exercise Execution Metadata
```
PATCH /workouts/{workout_id}/exercise-executions/{exercise_id}
```
**Request Body:**
```json
{
  "note_text": "Updated exercise notes",
  "exercise_order": 2
}
```
**Response (200):**
```json
{
  "exercise_id": 1,
  "exercise_name": "Push-ups",
  "exercise_order": 2,
  "note_text": "Updated exercise notes",
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-01T11:45:00Z",
  "sets": [
    {
      "id": 1,
      "exercise_id": 1,
      "note_text": "First set",
      "weight": 20.0,
      "clean_reps": 12,
      "forced_reps": 0,
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-01T10:30:00Z"
    }
  ]
}
```

### Reorder Exercises in Workout
```
PATCH /workouts/{workout_id}/exercise-executions/reorder
```
**Request Body:**
```json
{
  "exercise_ids": [3, 1, 2]
}
```
**Response (200):**
```json
{
  "message": "Exercise order updated successfully",
  "exercise_executions": [
    {
      "exercise_id": 3,
      "exercise_name": "Squats",
      "exercise_order": 1,
      "note_text": null,
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-01T11:50:00Z",
      "sets": []
    },
    {
      "exercise_id": 1,
      "exercise_name": "Push-ups",
      "exercise_order": 2,
      "note_text": "Updated exercise notes",
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-01T11:50:00Z",
      "sets": []
    },
    {
      "exercise_id": 2,
      "exercise_name": "Pull-ups",
      "exercise_order": 3,
      "note_text": null,
      "created_at": "2024-01-01T10:30:00Z",
      "updated_at": "2024-01-01T11:50:00Z",
      "sets": []
    }
  ]
}
```

---

## Sets (Nested under Exercise Executions)

### Add Single Set
```
POST /workouts/{workout_id}/exercise-executions/{exercise_id}/sets
```
**Request Body:**
```json
{
  "note_text": "First set, felt strong",
  "weight": 20.0,
  "clean_reps": 12,
  "forced_reps": 0
}
```
**Response (201):**
```json
{
  "id": 1,
  "exercise_id": 1,
  "note_text": "First set, felt strong",
  "weight": 20.0,
  "clean_reps": 12,
  "forced_reps": 0,
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-01T10:30:00Z"
}
```

### Update Single Set
```
PATCH /workouts/{workout_id}/exercise-executions/{exercise_id}/sets/{set_id}
```
**Request Body:**
```json
{
  "weight": 22.5,
  "clean_reps": 10,
  "note_text": "Increased weight"
}
```
**Response (200):**
```json
{
  "id": 1,
  "exercise_id": 1,
  "note_text": "Increased weight",
  "weight": 22.5,
  "clean_reps": 10,
  "forced_reps": 0,
  "created_at": "2024-01-01T10:30:00Z",
  "updated_at": "2024-01-01T11:15:00Z"
}
```

### Delete Single Set
```
DELETE /workouts/{workout_id}/exercise-executions/{exercise_id}/sets/{set_id}
```
**Response (204):** No content

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "validation_error",
  "message": "Invalid request data",
  "details": {
    "field_name": ["Field is required"]
  }
}
```

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "You don't have permission to access this resource"
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred"
}
```

---

## Notes

1. All timestamps are in ISO 8601 format (UTC)
2. All endpoints support pagination using `page` and `per_page` query parameters
3. Weight values are in pounds (float)
4. User can only access/modify their own workouts and exercises
5. System exercises (is_user_created=false) can be read by all users but only modified by admins
6. Nested resources follow RESTful conventions with proper parent-child relationships
7. Exercise modality enum values: `DUMBBELL`, `BARBELL`, `CABLE`, `MACHINE`, `SMITH`, `BODYWEIGHT`
8. Users with `is_admin=true` have additional permissions for managing system exercises (is_user_created=false)
9. Set IDs are autogenerated - do not include them in PUT requests for exercise-executions
10. Each exercise can only appear once per workout (business rule)
11. **Hybrid API Design**: Supports both bulk operations (PUT) and granular operations (individual PATCH/POST/DELETE)
12. **Exercise Reordering**: The reorder endpoint expects all exercise_ids currently in the workout
13. **Set Operations**: Individual sets can be added, updated, or deleted without affecting other sets
14. **Validation**: Finished workouts cannot be modified (exercise executions, sets, or reordering)
15. **Mobile-Friendly**: Individual set operations enable real-time recording during workouts
