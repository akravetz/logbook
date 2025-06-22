User
  id: bigint
  email_address: str
  google_id: str
  name: str 
  profile_image_url: str
  is_active: bool
  is_admin: bool

Exercise
  id: bigint
  name: str
  body_part: str
  modality: str (DUMBBELL, BARBELL, CABLE, MACHINE, SMITH, BODYWEIGHT)
  picture_url: str
  created_by_user_id: bigint
  updated_by_user_id: bigint
  created_at: timestamp
  updated_at: timestamp
  is_user_created: bool


Workout
  id: bigint
  finished_at: timestamp
  created_by_user_id: bigint
  updated_by_user_id: bigint
  created_at: timestamp
  updated_at: timestamp
  exercise_executions: list[ExerciseExecution]


ExerciseExecution
  exercise_id: bigint
  exercise_order: int
  sets: list[Set]
  note_text: str
  created_at: timestamp
  updated_at: timestamp

Set
  id: bigint
  exercise_id: bigint
  note_text: str
  weight: float
  clean_reps: int
  forced_reps: int
  created_at: timestamp
  updated_at: timestamp



