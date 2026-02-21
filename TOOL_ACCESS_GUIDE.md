# Aetios-Med Tool Access Guide

## Overview

All agent tools are now accessible via direct API calls from the UI, rather than through LLM function calling. This provides reliable access to all features while leveraging the OpenBioLLM-8B model for what it does best: medical Q&A.

## Architecture

- **Chat**: Uses minimal system prompt for excellent medical explanations
- **Tools**: Accessed via direct HTTP endpoints with frontend API methods
- **Model**: OpenBioLLM-8B (4.6GB GGUF) optimized for medical knowledge Q&A

## Tool Access Methods

### 1. Progress Tracking

#### Get Weak Topics
```typescript
import api from '@/services/api';

// Get topics with confidence below threshold
const weakTopics = await api.getWeakTopics(0.3);
// Returns: Array of { topic_id, confidence, last_studied, times_reviewed }
```

**Endpoint**: `GET /graph/weak-topics?threshold=0.3`

**UI Integration**: Dashboard → "Weak Areas" card

---

#### Get Decaying Topics (Spaced Repetition)
```typescript
// Get topics not reviewed in X days
const decayingTopics = await api.getDecayingTopics(7);
// Returns: Array of { topic_id, confidence, last_studied, days_since_review }
```

**Endpoint**: `GET /graph/decaying-topics?days=7`

**UI Integration**: Dashboard → "Topics Needing Review" card

---

#### Get Topic Details
```typescript
// Get detailed information about a topic
const topicDetails = await api.getTopicDetails('diabetes_mellitus');
// Returns: { topic_id, confidence, last_studied, resources, notes, progress }
```

**Endpoint**: `GET /graph/topic/{topic_id}`

**UI Integration**: Knowledge Graph → Click node → Detail panel

---

#### Get Curriculum Overview
```typescript
// Get overall progress statistics
const overview = await api.getCurriculumOverview();
// Returns: { total_topics, avg_confidence, categories_progress, weak_count }
```

**Endpoint**: `GET /graph/statistics`

**UI Integration**: Dashboard → Statistics cards

---

### 2. Knowledge Graph Navigation

#### Get Prerequisites
```typescript
// Get topics that should be mastered first
const prerequisites = await api.getPrerequisites('acute_coronary_syndrome');
// Returns: Array of prerequisite topic objects
```

**Endpoint**: `GET /graph/prerequisites/{topic_id}`

**UI Integration**: Knowledge Graph → Node detail → "Prerequisites" section

---

#### Get Dependent Topics
```typescript
// Get topics that build on this one
const dependents = await api.getDependentTopics('cell_biology');
// Returns: Array of dependent topic objects
```

**Endpoint**: `GET /graph/dependents/{topic_id}`

**UI Integration**: Knowledge Graph → Node detail → "What This Unlocks" section

---

### 3. Study Tools

#### Generate Quiz
```typescript
// Generate quiz for specific topics
const quiz = await api.generateQuiz(['diabetes_mellitus', 'insulin'], 5, 'sba');
// Returns: Array of QuizQuestion objects

// For SAQ (Short Answer Questions)
const saqQuiz = await api.generateQuiz(['pharmacology'], 3, 'saq');
```

**Endpoint**: `POST /quiz/generate`

**UI Integration**: Quiz Page → "Generate Quiz" button

---

#### Log Study Session
```typescript
// Track study time
const session = await api.startStudySession('cardiovascular_pathology');
// ... study ...
await api.endStudySession(session.id, { 
  duration: 45,  // minutes
  quality: 4,    // 1-5 rating
  notes: 'Reviewed ECG abnormalities'
});
```

**Endpoint**: `POST /study/session`

**UI Integration**: Study timer widget (can be added to any page)

---

#### Get Study History
```typescript
// Get past study sessions
const history = await api.getStudyHistory('diabetes_mellitus', 30);
// Returns: Array of { topic_id, duration, quality, session_date, notes }
```

**Endpoint**: `GET /study/sessions?topic_id={id}&limit=20`

**UI Integration**: Topic detail page → "Study History" tab

---

#### Generate Study Plan
```typescript
// Create personalized study plan
const plan = await api.generateStudyPlan(examId, {
  weeks: 4,
  hoursPerWeek: 15,
  focusAreas: ['weak_topics', 'spaced_repetition']
});
```

**Endpoint**: `POST /study/plan`

**UI Integration**: Study Plan page → "Generate Plan" button

---

### 4. Progress Updates

#### Update Confidence
```typescript
// Update confidence after self-assessment or quiz
await api.updateTopicConfidence('hypertension', 0.8, 'Reviewed NICE guidelines');
```

**Endpoint**: `POST /graph/confidence`

**UI Integration**: 
- Auto-updated after quiz completion
- Manual slider on topic detail pages

---

#### Log Quiz Result
```typescript
// Track quiz performance (auto-called by quiz submissions)
await api.logQuizResult('diabetes', true, 'What is HbA1c target?');
```

**Endpoint**: `POST /quiz/submit`

**UI Integration**: Auto-called when user submits quiz answer

---

### 5. Exam Preparation

#### Get Upcoming Exams
```typescript
// List all upcoming exams
const exams = await api.getExams();
// Returns: Array of { id, name, date, topics, created_at }
```

**Endpoint**: `GET /study/exams`

**UI Integration**: Dashboard → "Upcoming Exams" section

---

#### Add Exam
```typescript
// Create new exam to track
await api.createExam({
  name: 'Cardiovascular Finals',
  date: '2026-05-15',
  topics: ['heart_failure', 'arrhythmias', 'acs']
});
```

**Endpoint**: `POST /study/exam`

**UI Integration**: Exams page → "Add Exam" button

---

#### Get Exam Readiness
```typescript
// Assess preparedness for an exam
const readiness = await api.getExamReadiness(examId);
// Returns: { 
//   readiness_score: 0.75,
//   topics_ready: 12,
//   topics_weak: 3,
//   recommended_hours: 6
// }
```

**Endpoint**: `GET /study/readiness/{exam_id}`

**UI Integration**: Exam detail page → "Readiness" progress bar

---

### 6. Notes & Resources

#### Search Notes
```typescript
// Search through personal notes
const notes = await api.searchNotes('loop diuretics', 5);
// Returns: Array of { id, topic_id, title, content, created_at }
```

**Endpoint**: `GET /graph/search-notes?query={q}&limit=5`

**UI Integration**: Search bar → Notes filter

---

#### Get Anki Stats
```typescript
// Get flashcard statistics
const ankiStats = await api.getAnkiStats('pharmacology');
// Returns: { cards_due, cards_mastered, retention_rate, last_sync }
```

**Endpoint**: `GET /ingest/anki/due?topic_id={id}`

**UI Integration**: Dashboard → "Anki Status" widget

---

#### Get Semester Scopes
```typescript
// List curriculum scopes
const scopes = await api.getSemesterScopes();
// Returns: Array of semester scope objects

// Get active scope
const activeScope = await api.getActiveSemesterScope();
```

**Endpoint**: `GET /semester/scopes`

**UI Integration**: Settings → "Semester Scopes" tab

---

## Implementation Examples

### Dashboard Widget Example

```typescript
// Dashboard component using multiple tools
const Dashboard = () => {
  const [weakTopics, setWeakTopics] = useState([]);
  const [decayingTopics, setDecayingTopics] = useState([]);
  const [upcomingExams, setUpcomingExams] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      const [weak, decaying, exams, overview] = await Promise.all([
        api.getWeakTopics(0.3),
        api.getDecayingTopics(7),
        api.getExams(),
        api.getCurriculumOverview()
      ]);
      
      setWeakTopics(weak);
      setDecayingTopics(decaying);
      setUpcomingExams(exams);
      setStats(overview);
    };
    
    loadData();
  }, []);

  return (
    <div>
      <StatsOverview stats={stats} />
      <WeakAreasCard topics={weakTopics} />
      <DecayingTopicsCard topics={decaying} />
      <UpcomingExamsCard exams={upcomingExams} />
    </div>
  );
};
```

### Study Session Tracker

```typescript
// Study session timer component
const StudyTimer = ({ topicId }) => {
  const [sessionId, setSessionId] = useState(null);
  const [startTime, setStartTime] = useState(null);

  const startSession = async () => {
    const session = await api.startStudySession(topicId);
    setSessionId(session.id);
    setStartTime(Date.now());
  };

  const endSession = async (quality) => {
    const duration = Math.round((Date.now() - startTime) / 60000);
    await api.endStudySession(sessionId, { duration, quality });
    setSessionId(null);
    setStartTime(null);
  };

  return (
    <div>
      {!sessionId ? (
        <button onClick={startSession}>Start Studying</button>
      ) : (
        <>
          <Timer startTime={startTime} />
          <RatingButtons onRate={endSession} />
        </>
      )}
    </div>
  );
};
```

### Quiz Flow

```typescript
// Complete quiz generation and submission
const QuizPage = () => {
  const generateAndTakeQuiz = async () => {
    // 1. Generate quiz
    const questions = await api.generateQuiz(['diabetes'], 5, 'sba');
    
    // 2. Display questions and collect answers
    const userAnswer = await showQuestion(questions[0]);
    
    // 3. Submit answer (auto-logs result and updates confidence)
    const result = await api.submitQuizAnswer(
      questions[0].id,
      userAnswer
    );
    
    // 4. Show feedback
    showFeedback(result.correct, result.explanation);
  };
};
```

## Chat Integration

The chat interface focuses on medical Q&A without attempting tool calling:

```typescript
const ChatInterface = () => {
  const sendMessage = async (message: string) => {
    // Send to backend for medical Q&A response
    const response = await api.sendMessage(message);
    
    // Display response
    addMessage({ role: 'assistant', content: response.message });
  };
  
  // For tool functionality, use dedicated UI controls
  const showProgress = async () => {
    const weak = await api.getWeakTopics();
    displayWeakTopicsDialog(weak);
  };
};
```

## Migration Notes

- **Old**: LLM tried to call tools → Failed due to 8B model limitations
- **New**: UI calls tools directly → Reliable, fast, better UX
- **Chat**: Now optimized for medical explanations (works perfectly)
- **Tools**: Full functionality preserved via direct API access

## Benefits

1. **Reliability**: Direct API calls vs unreliable LLM function calling
2. **Performance**: No overhead from tool parsing/execution in LLM context
3. **UX**: Better user control with explicit buttons/widgets
4. **Model**: OpenBioLLM-8B excels at medical Q&A (its designed purpose)
5. **Maintainability**: Clear separation between Q&A and tool functionality

## Testing

All endpoints have been tested and are functional. Example test:

```bash
# Test weak topics
curl http://localhost:8741/api/graph/weak-topics?threshold=0.3

# Test quiz generation
curl -X POST http://localhost:8741/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"topic_ids": ["diabetes"], "num_questions": 3, "difficulty": "medium"}'

# Test study session
curl -X POST http://localhost:8741/api/study/session \
  -H "Content-Type: application/json" \
  -d '{"topic_id": "diabetes", "duration": 30, "quality": 4}'
```

## Frontend Integration Status

- ✅ API methods added to `src/services/api.ts`
- ✅ Backend endpoints implemented and tested
- ⏳ UI components (Dashboard, Quiz, etc.) already exist
- ⏳ Can add new widgets/buttons as needed

All tools are now accessible - use the API methods above to integrate them into UI components!
