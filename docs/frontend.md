# Frontend Design Specification
## Workout Tracking App

**Target**: Mobile-first, gym-optimized workout tracking interface
**Technology**: Next.js 14 + TypeScript + ShadCN UI + Tailwind CSS
**Primary Use Case**: Quick workout logging during gym sessions

---

## Executive Summary

Design a beautiful, lightning-fast mobile interface optimized for gym use. Users need to log workouts effortlessly while exercising - every interaction must be thumb-friendly, glanceable, and completed in under 5 seconds.

### Core Design Principles
- **Speed First**: Every action completes in < 5 seconds
- **Thumb Navigation**: All controls reachable one-handed
- **Glanceable Information**: Clear at arm's length while exercising
- **Minimal Cognitive Load**: Focus on workout, not the app
- **Forgiving Interface**: Easy to edit and undo mistakes

---

## User Experience Framework

### Primary User Journey
```
Login → Start Workout → Add Exercise → Log Sets → Finish Workout
  ↓        ↓             ↓           ↓         ↓
 <3s      <2s          <10s        <5s/set   <3s
```

### User Personas

**Primary: "Gym Regular" (Sarah, 28)**
- Lifts 4x/week, follows structured programs
- Uses phone between sets for 30-60 seconds
- Values speed and simplicity over features

**Secondary: "Casual Lifter" (Mike, 35)**
- Lifts 2x/week, flexible routine
- Wants to track progress without complexity
- May forget exercises between sessions

### Critical User Scenarios

**Scenario 1: Mid-Workout Set Logging**
- User just finished a set of bench press
- Has 90 seconds rest before next set
- Needs to log: 185 lbs × 8 reps
- Then see what they did last time

**Scenario 2: Exercise Selection**
- Starting workout, needs to add leg press
- Can't remember exact machine name
- Wants to see previous weights used
- Needs to start first set immediately

**Scenario 3: Quick Workout Review**
- Finished workout, heading home
- Wants to glance at what was accomplished
- May want to add quick notes about how it felt

---

## Visual Design System

### Color Palette
```css
/* Primary Brand Colors */
--primary: 217 91% 60%        /* Energetic blue #2563eb */
--primary-foreground: 0 0% 98%

/* Gym Environment Optimized */
--background: 0 0% 8%         /* Dark mode default #141414 */
--foreground: 0 0% 95%        /* High contrast text */
--muted: 0 0% 15%            /* Card backgrounds #262626 */
--accent: 142 76% 36%        /* Success green #16a34a */
--destructive: 0 84% 60%     /* Warning red #dc2626 */

/* Workout Status Colors */
--in-progress: 25 95% 53%    /* Active orange #f97316 */
--completed: 142 76% 36%     /* Completed green */
--rest-timer: 217 91% 60%    /* Rest blue */
```

### Typography Scale
```css
/* Optimized for mobile readability */
--text-display: 3rem    /* Workout titles */
--text-large: 1.5rem    /* Set numbers, weights */
--text-body: 1rem       /* Exercise names */
--text-small: 0.875rem  /* Secondary info */
--text-micro: 0.75rem   /* Timestamps, notes */
```

### Spacing System
```css
/* Touch-optimized spacing */
--space-thumb: 3rem     /* 48px - minimum touch target */
--space-comfortable: 1rem /* 16px - comfortable spacing */
--space-tight: 0.5rem   /* 8px - compact layouts */
```

---

## Core Components Specification

### 1. Navigation Shell
**Component**: `AppShell`
```
┌─────────────────────────┐
│ [User Avatar] [Settings]│ ← Header (56px height)
├─────────────────────────┤
│                         │
│    Main Content Area    │ ← Dynamic content
│                         │
├─────────────────────────┤
│ [Home][Workout][History]│ ← Bottom nav (72px)
└─────────────────────────┘
```

**Specifications**:
- Fixed header with user context
- Bottom navigation (3 primary tabs)
- Safe area handling for iOS/Android
- Dark theme optimized for gym lighting

### 2. Workout Active State
**Component**: `WorkoutInterface`
```
┌─────────────────────────┐
│ ⏱️ 45:23    [Finish]    │ ← Timer + finish button
├─────────────────────────┤
│ 💪 Bench Press          │ ← Current exercise
│ Last: 185×8+2, 185×6    │ ← Previous session data with forced reps
├─────────────────────────┤
│ Set 1: [185] × [8+2] ✓  │ ← Completed sets (clean + forced)
│ Set 2: [185] × [6] ✓    │
│ Set 3: [185] × [?+?] ○  │ ← Current set (large)
├─────────────────────────┤
│ [- Weight -] [Clean Reps] │ ← Input controls (48px)
│ [Forced Reps] [Complete] │ ← Forced reps + primary action
└─────────────────────────┘
```

**Key Features**:
- One-handed operation with forced reps support
- Smart defaults from previous sets (clean + forced)
- Large, thumb-friendly inputs for all values
- Visual progress indicators showing clean+forced format
- Optional forced reps (defaults to 0, can be skipped)
- Undo last set capability

### 3. Exercise Search/Selection
**Component**: `ExerciseSelector`
```
┌─────────────────────────┐
│ 🔍 [Search exercises...] │ ← Search with autocomplete
├─────────────────────────┤
│ 📝 Recent Exercises      │
│ • Bench Press    [+]    │ ← Quick add from recents
│ • Squat          [+]    │
│ • Deadlift       [+]    │
├─────────────────────────┤
│ 🏷️ Browse by Category   │
│ [Chest] [Back] [Legs]   │ ← Category filters
│ [Shoulders] [Arms] [More]│
└─────────────────────────┘
```

**Interaction Flow**:
1. Tap search → keyboard with exercise suggestions
2. Tap recent → immediately add to workout
3. Tap category → filtered grid view
4. Long press → preview exercise details

### 4. Set Input Controls
**Component**: `SetInput`
```
┌─────────────────────────┐
│        Weight (lbs)     │
│    ┌─────────────────┐  │
│ [-]│      185        │[+]│ ← Steppers for quick adjust
│    └─────────────────┘  │
│                         │
│       Clean Reps        │
│    ┌─────────────────┐  │
│ [-]│       8         │[+]│ ← Primary rep count
│    └─────────────────┘  │
│                         │
│     Forced Reps (opt)   │
│    ┌─────────────────┐  │
│ [-]│       2         │[+]│ ← Optional, defaults to 0
│    └─────────────────┘  │
│                         │
│ [Complete Set] 🎯       │ ← Large success button
└─────────────────────────┘
```

**Behavior**:
- Default to previous set values (weight + clean reps)
- Forced reps defaults to 0, can be skipped
- Stepper buttons for ±5 lbs, ±1 rep
- Direct tap for keyboard input
- Display format: "185 × 8+2" or "185 × 8" (no forced)
- Haptic feedback on completion

---

## Screen Layouts & User Flows

### 1. Authentication Flow
**Screen**: `LoginScreen`
```
┌─────────────────────────┐
│                         │
│      💪 LogBk           │ ← App branding
│   Track Your Gains      │
│                         │
│                         │
│  [Sign in with Google]  │ ← Single auth method
│         🔐              │
│                         │
│  Simple workout tracking│
│    for serious lifters  │ ← Value proposition
└─────────────────────────┘
```

### 2. Dashboard/Home
**Screen**: `DashboardScreen`
```
┌─────────────────────────┐
│ Good morning, Sarah! 👋 │ ← Personalized greeting
├─────────────────────────┤
│ 🔥 3 day streak         │ ← Motivation metric
│ 💪 12 workouts this month│
├─────────────────────────┤
│ [Start New Workout] ⚡  │ ← Primary CTA (large)
├─────────────────────────┤
│ 📊 Recent Activity      │
│                         │
│ Mon: Push (45 min) ✅   │ ← Recent workouts
│ Fri: Pull (52 min) ✅   │
│ Wed: Legs (38 min) ✅   │
├─────────────────────────┤
│ [View All History] →    │
└─────────────────────────┘
```

### 3. Exercise Library
**Screen**: `ExerciseLibraryScreen`
```
┌─────────────────────────┐
│ 🔍 [Search exercises...] │
├─────────────────────────┤
│ 🏷️ [Chest][Back][Legs]  │ ← Filter chips
│    [Arms][Shoulders][+] │
├─────────────────────────┤
│ Bench Press        🏋️‍♂️  │ ← Exercise cards
│ Barbell • Last: 185×8+2 │   with context & forced reps
│ ────────────────────    │
│ Incline Press      📈   │
│ Dumbbell • Last: 70×10  │
│ ────────────────────    │
│ Dips              💪   │
│ Bodyweight • Last: +25×8+1│
└─────────────────────────┘
```

### 4. Workout History
**Screen**: `WorkoutHistoryScreen`
```
┌─────────────────────────┐
│ 📊 Workout History      │
├─────────────────────────┤
│ This Week: 3 workouts   │ ← Summary stats
│ Last Week: 2 workouts   │
├─────────────────────────┤
│ Today - Push Day ✅     │ ← Workout entries
│ 6 exercises • 45 min    │
│ ─ Bench: 185×8+2,8,6    │ ← Exercise summary with forced reps
│ ─ Incline: 155×10,9+1,8 │
│ [View Details] →        │
│                         │
│ Mon - Pull Day ✅       │
│ 5 exercises • 52 min    │
│ [View Details] →        │
└─────────────────────────┘
```

---

## Advanced Interaction Patterns

### Gesture Controls
- **Pull down**: Refresh current screen
- **Swipe right**: Go back/undo last action
- **Long press**: Access secondary actions
- **Double tap**: Quick complete (sets)

### Smart Defaults & Predictive Input
- **Weight**: Default to last successful weight for that exercise
- **Clean Reps**: Suggest rep ranges based on recent performance
- **Forced Reps**: Optional field, defaults to 0, remembers last forced rep count
- **Exercise Order**: Remember preferred exercise sequences
- **Rest Timer**: Auto-start based on exercise type

### Forced Reps Pattern
- **Display Format**: `185 × 8+2` (weight × clean reps + forced reps)
- **Input Flow**: Weight → Clean Reps → Forced Reps (optional) → Complete
- **Data Storage**: Store clean_reps and forced_reps separately in backend
- **UI Behavior**: Forced reps field can be skipped (stays 0) or tapped to activate
- **Smart Defaults**: If user did forced reps last set, suggest same count

### Haptic Feedback Patterns
- **Light tap**: Button press confirmation
- **Medium tap**: Set completion
- **Heavy tap**: Workout milestone (PR, streak)
- **Error pattern**: Invalid input or network error

---

## Technical Implementation Notes

### Performance Requirements
- **Initial Load**: < 2 seconds on 3G
- **Set Logging**: < 300ms response time
- **Search Results**: < 500ms from keystroke
- **Offline Capability**: Core logging works without network

### Responsive Breakpoints
```css
/* Mobile-first approach */
--mobile: 390px         /* iPhone 14 Pro baseline */
--mobile-lg: 414px      /* iPhone 14 Pro Max */
--tablet: 768px         /* iPad mini */
--desktop: 1024px       /* Optional desktop view */
```

### Component Architecture
```
/components
├── ui/                 # ShadCN base components
├── workout/            # Workout-specific components
│   ├── SetInput.tsx
│   ├── ExerciseCard.tsx
│   └── WorkoutTimer.tsx
├── exercise/           # Exercise management
│   ├── ExerciseSearch.tsx
│   └── ExerciseSelector.tsx
└── layout/             # Layout components
    ├── AppShell.tsx
    └── BottomNav.tsx
```

### State Management Strategy
- **Server State**: React Query for API data
- **Workout State**: Zustand for active workout
- **UI State**: React hooks for component state
- **Persistent State**: localStorage for user preferences

---

## Accessibility & Usability

### Accessibility Features
- **High Contrast**: Optimized for various lighting conditions
- **Large Touch Targets**: Minimum 44px tap areas
- **Screen Reader**: Proper ARIA labels for all interactions
- **Keyboard Navigation**: Full keyboard accessibility
- **Motion Reduced**: Respect user motion preferences

### Gym Environment Considerations
- **Gloved Hands**: Larger touch targets, no fine gestures
- **Bright/Dim Lighting**: High contrast, adjustable brightness
- **Quick Interactions**: Minimal scrolling, obvious CTAs
- **Sweaty Phones**: Prevent accidental touches
- **Orientation Lock**: Portrait mode optimized

### Error Handling & Edge Cases
- **Network Loss**: Graceful offline mode with sync
- **Battery Saving**: Optimized for extended gym sessions
- **Interruptions**: Auto-save progress, resume capability
- **Input Validation**: Immediate feedback on invalid data

---

## Success Metrics & Testing

### User Experience KPIs
- **Set Logging Speed**: < 5 seconds average
- **Workout Completion Rate**: > 90%
- **User Retention**: > 80% weekly active
- **Error Recovery**: < 2 taps to fix mistakes

### Testing Strategy
- **Usability Testing**: Real gym environment testing
- **Performance Testing**: 3G network simulation
- **Accessibility Testing**: Screen reader compatibility
- **Cross-Device Testing**: iOS Safari, Android Chrome

### A/B Testing Opportunities
- **Input Methods**: Steppers vs. direct keyboard
- **Default Values**: Previous weight vs. progressive overload
- **Completion Feedback**: Animation styles and duration
- **Exercise Suggestions**: Recency vs. frequency based

---

## Implementation Roadmap

### Phase 1: Core MVP (Week 1-2)
- Authentication flow with Google SSO
- Basic workout creation and set logging
- Exercise search and selection
- Simple history view

### Phase 2: Enhanced UX (Week 3-4)
- Smart defaults and predictive input
- Workout timer and rest tracking
- Improved exercise library with filtering
- Offline capability

### Phase 3: Polish & Optimization (Week 5-6)
- Advanced gestures and haptic feedback
- Performance optimization
- Comprehensive error handling
- Real gym user testing

This specification provides a complete foundation for building a world-class mobile workout tracking interface that prioritizes speed, usability, and the unique constraints of gym environments.
