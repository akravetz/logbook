# Frontend Development Guide

This document provides comprehensive guidance for developing and maintaining the LogBK frontend application.

## Architecture Overview

The frontend is built with **Next.js 15 App Router** and follows a **mobile-first, component-driven architecture** optimized for workout tracking and gym usage.

### Core Technologies
- **Next.js 15** with App Router for file-based routing
- **TypeScript** for type safety and developer experience
- **Tailwind CSS** for utility-first styling
- **shadcn/ui** for consistent component design system
- **Zustand** for client-side state management
- **TanStack Query** for server state and caching
- **NextAuth.js** for authentication
- **Framer Motion** for animations

### Architecture Principles
- **Mobile-first design** optimized for gym usage
- **Type-safe API integration** with auto-generated clients
- **Semantic cache management** for optimal performance
- **Touch-friendly interactions** with gesture support
- **Real-time workout tracking** with timer and state persistence

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Home page (workout list or login)
│   ├── workout/[id]/      # Dynamic workout pages
│   ├── exercises/         # Exercise browser
│   ├── profile/           # User profile
│   └── api/auth/         # NextAuth API routes
├── components/            # React components
│   ├── screens/          # Full-page components
│   ├── modals/           # Modal dialogs
│   ├── layout/           # Layout components
│   └── ui/               # shadcn/ui components
├── lib/                  # Utilities and configurations
│   ├── api/              # Auto-generated API client
│   ├── contexts/         # React contexts
│   ├── hooks/            # Custom React hooks
│   ├── stores/           # Zustand stores
│   └── utils.ts          # Utility functions
└── types/                # TypeScript type definitions
```

## Next.js App Router Patterns

### Root Layout Configuration

**Location**: `app/layout.tsx`

```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} font-sans`}>
        <ReactQueryProvider>
          <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
            <AuthProvider>
              <WorkoutProvider>
                <MobileLayout>
                  {children}
                </MobileLayout>
              </WorkoutProvider>
            </AuthProvider>
          </ThemeProvider>
        </ReactQueryProvider>
      </body>
    </html>
  )
}
```

**Key Features**:
- **Provider composition** with React Query, Auth, Theme, and Workout contexts
- **Mobile-optimized viewport** configuration
- **Custom font loading** with Geist Sans
- **Hydration optimization** with suppressHydrationWarning

### Route Organization

```
app/
├── page.tsx                    # Home: workout list or login redirect
├── workout/[id]/page.tsx       # Active workout tracking interface
├── exercises/page.tsx          # Exercise browser and search
├── profile/page.tsx            # User profile and settings
└── api/auth/[...nextauth]/     # NextAuth API routes
    └── route.ts
```

**Routing Patterns**:
- **Dynamic routes** for individual workouts
- **Conditional rendering** based on authentication state
- **Mobile-optimized navigation** with bottom tab bar
- **Deep linking** support for workout sharing

## Component Architecture

### Screen-Based Organization

**Screen Components** (`components/screens/`):
- `active-workout-screen.tsx` - Real-time workout tracking interface
- `workouts-list-screen.tsx` - Workout history and management
- `login-screen.tsx` - Authentication interface

**Design Patterns**:
```tsx
// Screen component pattern
interface ActiveWorkoutScreenProps {
  workoutId: number
}

export function ActiveWorkoutScreen({ workoutId }: ActiveWorkoutScreenProps) {
  // State management
  const { activeWorkout, setActiveWorkout } = useWorkoutStore()
  const { invalidateWorkoutData } = useCacheUtils()

  // Data fetching
  const { data: workout, isLoading } = useGetWorkout(workoutId)

  // Business logic
  const handleFinishWorkout = async () => {
    await finishWorkoutMutation.mutateAsync()
    await invalidateWorkoutData()
    router.push('/')
  }

  return (
    <div className="mobile-screen">
      {/* Screen content */}
    </div>
  )
}
```

### Modal-Driven Interactions

**Modal Components** (`components/modals/`):
- `add-exercise-modal.tsx` - Exercise selection and addition
- `add-set-modal.tsx` - Set logging with weight/reps
- `edit-set-modal.tsx` - Set modification interface
- `voice-note-modal.tsx` - Voice recording for exercise notes

**Modal State Management**:
```tsx
// UI Store pattern for modal management
interface UIState {
  modals: {
    addExercise: { isOpen: boolean; workoutId?: number }
    addSet: { isOpen: boolean; exerciseId?: number; exerciseData?: any }
    editSet: { isOpen: boolean; setId?: number; currentData?: any }
    voiceNote: { isOpen: boolean; exerciseId?: number; exerciseName?: string }
  }

  // Modal actions
  openAddExerciseModal: (workoutId: number) => void
  closeAddExerciseModal: () => void
  // ... other modal actions
}
```

### UI Component System

**shadcn/ui Integration**:
```tsx
// Button component with variant system
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
  }
)
```

## State Management Architecture

### Zustand Store Pattern

**Workout Store** (`lib/stores/workout-store.ts`):
```tsx
interface WorkoutState {
  // State
  activeWorkout: WorkoutResponse | null
  workoutTimer: number
  timerInterval: NodeJS.Timeout | null

  // Actions
  setActiveWorkout: (workout: WorkoutResponse | null) => void
  startTimer: () => void
  stopTimer: () => void
  addExerciseToWorkout: (exercise: ExerciseExecutionResponse) => void
  updateExerciseInWorkout: (exercise: ExerciseExecutionResponse) => void
  removeExerciseFromWorkout: (exerciseId: number) => void
  reorderExercises: (exercises: ExerciseExecutionResponse[]) => void
}

export const useWorkoutStore = create<WorkoutState>((set, get) => ({
  // Implementation with immutable updates
  addExerciseToWorkout: (exercise) =>
    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: [...(state.activeWorkout.exercise_executions || []), exercise],
          }
        : null,
    })),
}))
```

**UI Store** (`lib/stores/ui-store.ts`):
```tsx
interface UIState {
  modals: {
    addExercise: { isOpen: boolean; workoutId?: number }
    // ... other modals
  }

  // Modal management actions
  openAddExerciseModal: (workoutId: number) => void
  closeAddExerciseModal: () => void
}
```

**Store Design Principles**:
- **Single responsibility** - Each store handles one domain
- **Immutable updates** - Always create new objects for state changes
- **Typed actions** - Full TypeScript support for actions and state
- **Minimal state** - Only store what can't be derived

### Server State with TanStack Query

**Query Configuration**:
```tsx
// React Query client configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})
```

**Semantic Cache Tags**:
```tsx
export const CACHE_TAGS = {
  WORKOUT_DATA: 'workout-data',
  EXERCISE_DATA: 'exercise-data',
  USER_DATA: 'user-data',
  SESSION_DATA: 'session-data',
} as const

// Usage in generated hooks
export const useTaggedListWorkouts = () => {
  return useListWorkouts({
    query: {
      meta: { tags: [CACHE_TAGS.WORKOUT_DATA] }
    }
  })
}
```

## API Integration Patterns

### Auto-Generated Client

**Orval Configuration** (`orval.config.ts`):
```tsx
export default defineConfig({
  workoutApi: {
    input: "openapi.json",
    output: {
      mode: "single",
      target: "lib/api/generated.ts",
      schemas: "lib/api/model",
      client: "react-query",
      override: {
        mutator: {
          path: "lib/api/mutator.ts",
          name: "customInstance",
        },
      },
    },
  },
})
```

**API Client Features**:
- **Auto-generated** from OpenAPI spec
- **Type-safe** request/response handling
- **TanStack Query integration** with hooks
- **Custom axios instance** with authentication

### Authentication Integration

**Axios Interceptors** (`lib/api/mutator.ts`):
```tsx
// Request interceptor for token injection
AXIOS_INSTANCE.interceptors.request.use(async (config) => {
  const session = await getSession()

  if (session?.sessionToken) {
    config.headers.Authorization = `Bearer ${session.sessionToken}`
  }

  return config
})

// Response interceptor for auth error handling
AXIOS_INSTANCE.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      await signOut({ callbackUrl: "/" })
    }
    return Promise.reject(error)
  }
)
```

### Cache Management System

**Semantic Cache Invalidation** (`lib/cache-tags.ts`):
```tsx
export const useCacheUtils = () => {
  const queryClient = useQueryClient()

  return {
    // Invalidate workout-related data after mutations
    invalidateWorkoutData: () => cacheUtils.invalidateByTags(queryClient, [
      CACHE_TAGS.WORKOUT_DATA,
      CACHE_TAGS.WORKOUT_STATS
    ]),

    // Invalidate exercise data after creation/modification
    invalidateExerciseData: () => cacheUtils.invalidateByTags(queryClient, [
      CACHE_TAGS.EXERCISE_DATA,
      CACHE_TAGS.EXERCISE_CATEGORIES
    ]),
  }
}
```

**Usage Pattern**:
```tsx
const { invalidateWorkoutData } = useCacheUtils()

const mutation = useCreateWorkoutMutation({
  onSuccess: async () => {
    await invalidateWorkoutData() // Semantic cache invalidation
  }
})
```

## Authentication Patterns

### NextAuth Configuration

**Auth Provider** (`lib/contexts/auth-context.tsx`):
```tsx
export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <SessionProvider>
      {children}
    </SessionProvider>
  )
}

// Export convenience hook
export { useSession as useAuth } from "next-auth/react"
```

**Authentication Flow**:
1. **Google OAuth** login with NextAuth
2. **Token verification** with backend
3. **Session token** storage in JWT
4. **Automatic API authentication** via Axios interceptors
5. **401 handling** with forced logout

**Route Protection Pattern**:
```tsx
export default function ProtectedPage() {
  const { data: session, status } = useAuth()

  if (status === "loading") return <LoadingScreen />
  if (!session) return <LoginScreen />

  return <AuthenticatedContent />
}
```

## UI/UX Patterns

### Mobile-First Design

**Viewport Configuration**:
```tsx
export const metadata: Metadata = {
  viewport: "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no",
}
```

**Touch-Optimized Interactions**:
```tsx
// Minimum 48px touch targets
<button className="min-h-[48px] min-w-[48px] touch-manipulation">
  <Icon className="w-6 h-6" />
</button>

// Touch-friendly drag handles
<button
  {...attributes}
  {...listeners}
  className="touch-none p-1 rounded hover:bg-gray-100 cursor-grab active:cursor-grabbing"
>
  <GripVertical className="w-5 h-5 text-gray-400" />
</button>
```

### Gesture Support

**Drag and Drop with dnd-kit**:
```tsx
function SortableExerciseCard({ execution }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: execution.exercise_id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} className="sortable-item">
      <button {...attributes} {...listeners} className="drag-handle">
        <GripVertical />
      </button>
      {/* Content */}
    </div>
  )
}
```

### Styling System

**Tailwind Configuration**:
```tsx
// tailwind.config.ts
export default {
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // CSS custom properties for theme support
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

**CSS Custom Properties** (`app/globals.css`):
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  /* ... other color variables */
}

/* Gym-friendly high contrast mode */
.high-contrast {
  --background: 0 0% 5%;
  --foreground: 0 0% 95%;
  /* Enhanced contrast for gym lighting */
}
```

**Component Styling Patterns**:
```tsx
// Utility class composition
<div className="mobile-screen bg-background text-foreground">
  <div className="workout-header p-4 border-b border-border">
    <h1 className="text-2xl font-bold">Active Workout</h1>
  </div>
</div>

// Conditional styling for states
<div className={cn(
  "exercise-card bg-card rounded-lg shadow-sm",
  isDragging && "shadow-lg ring-2 ring-primary/20",
  isFinished && "opacity-60"
)}>
```

## Custom Hooks & Utilities

### Debounce Hook

```tsx
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}
```

### Cache Utilities Hook

```tsx
export function useCacheUtils() {
  const queryClient = useQueryClient()

  return {
    invalidateWorkoutData: () => cacheUtils.invalidateWorkoutData(queryClient),
    invalidateExerciseData: () => cacheUtils.invalidateExerciseData(queryClient),
    invalidateUserData: () => cacheUtils.invalidateUserData(queryClient),
    invalidateAll: () => cacheUtils.invalidateAll(queryClient)
  }
}
```

## Development Workflow

### API Development Integration

```bash
# Refresh API client from backend
npm run refresh-api    # Update OpenAPI spec + regenerate client

# Development with API sync
npm run dev:full       # Refresh API + start dev server

# Manual API generation
npm run generate-api   # Generate client from existing OpenAPI spec
```

### Build Process

```bash
# Development
npm run dev           # Next.js dev server with hot reloading

# Production
npm run build         # Optimized production build
npm run start         # Production server

# Code quality
npm run lint          # ESLint checks
```

## Performance Optimizations

### Query Caching Strategy

- **5-minute stale time** for most queries
- **Semantic tag-based invalidation** for related data
- **Optimistic updates** for immediate UI feedback
- **Background refetching** disabled to preserve mobile data

### Code Splitting

- **Route-based splitting** with Next.js App Router
- **Component lazy loading** for modals and heavy components
- **API client tree shaking** with auto-generated imports

### Mobile Optimizations

- **Touch manipulation** CSS for better responsiveness
- **Viewport optimization** with zoom restrictions
- **Minimal JavaScript** for core workout tracking
- **Offline-first considerations** for gym environments

## Testing Considerations

### Component Testing Patterns

```tsx
// Test workout store integration
test('should add exercise to active workout', () => {
  const { result } = renderHook(() => useWorkoutStore())

  act(() => {
    result.current.setActiveWorkout(mockWorkout)
    result.current.addExerciseToWorkout(mockExercise)
  })

  expect(result.current.activeWorkout?.exercise_executions).toHaveLength(1)
})
```

### API Integration Testing

```tsx
// Test cache invalidation
test('should invalidate workout data after mutation', async () => {
  const queryClient = new QueryClient()
  const { invalidateWorkoutData } = cacheUtils

  const spy = jest.spyOn(queryClient, 'invalidateQueries')
  await invalidateWorkoutData(queryClient)

  expect(spy).toHaveBeenCalledWith({
    predicate: expect.any(Function)
  })
})
```

## Deployment Considerations

### Environment Configuration

```bash
# Production environment variables
NEXT_PUBLIC_API_URL=https://api.logbk.app
NEXTAUTH_URL=https://logbk.app
NEXTAUTH_SECRET=your-production-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Build Optimizations

- **Image optimization** with Next.js Image component
- **Font optimization** with next/font
- **Bundle analysis** for identifying optimization opportunities
- **Progressive Web App** features for mobile installation

## Key Architectural Decisions

### Why Zustand over Redux
- **Minimal boilerplate** for simple state needs
- **TypeScript-first** design
- **Small bundle size** critical for mobile performance
- **Easy testing** without complex setup

### Why TanStack Query
- **Server state specialization** vs client state
- **Automatic caching** and background updates
- **Optimistic updates** for better UX
- **DevTools** for debugging cache behavior

### Why shadcn/ui
- **Copy-paste components** instead of package dependency
- **Full customization** control
- **TypeScript native** with excellent DX
- **Consistent design system** with variants

This architecture provides a robust foundation for mobile-first workout tracking with excellent developer experience, type safety, and performance optimization for gym environments.
