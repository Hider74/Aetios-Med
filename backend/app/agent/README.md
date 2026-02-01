# Aetios Agent System

The Aetios agent is an AI-powered medical tutor designed for UK medical students. It uses a tool-calling architecture to provide personalized, data-driven learning guidance.

## Architecture

The agent system consists of three main components:

### 1. Tools (`tools.py`)

Defines 17 specialized tools for accessing student data and performing actions:

**Knowledge Graph & Progress Tracking:**
- `get_weak_topics(threshold)` - Find topics with low confidence
- `get_decaying_topics(days)` - Find topics needing review
- `get_prerequisites(topic_id)` - Get prerequisite topics
- `get_dependent_topics(topic_id)` - Get dependent topics
- `get_topic_details(topic_id)` - Get topic details and stats
- `get_curriculum_overview()` - Get full curriculum structure

**Learning Resources:**
- `search_notes(query, limit)` - Search student's notes
- `get_anki_stats(topic_id)` - Get flashcard statistics
- `open_resource(url)` - Open learning resources

**Assessment:**
- `generate_quiz(topic_id, num_questions, difficulty)` - Generate quizzes
- `log_quiz_result(topic_id, correct, question)` - Track quiz performance

**Study Planning:**
- `log_study_session(topic_id, duration, notes)` - Log study time
- `get_study_history(topic_id, days)` - View study history
- `generate_study_plan(exam_id, weeks)` - Create study plans
- `get_exam_readiness(exam_id)` - Assess exam readiness

**Exam Management:**
- `add_exam(name, date, topics)` - Add new exam
- `get_upcoming_exams()` - List upcoming exams

**Progress Updates:**
- `update_confidence(topic_id, confidence, notes)` - Update topic confidence

All tools are defined in OpenAI function-calling format for seamless integration with GPT-4.

### 2. Prompts (`prompts.py`)

Manages prompt templates loaded from `data/prompts/`:

- **`tutor_system.txt`** - Main system prompt defining Aetios's identity, capabilities, and behavior
- **`quiz_generation.txt`** - Detailed instructions for generating UK medical school quizzes
- **`study_plan.txt`** - Guidelines for creating personalized study plans

The `PromptManager` class handles loading and accessing prompts with caching.

### 3. Orchestrator (`orchestrator.py`)

The `AgentOrchestrator` class manages the agent conversation loop:

- Maintains conversation history
- Calls OpenAI API with tools
- Executes tool calls
- Handles multi-turn interactions
- Supports streaming responses
- Conversation export/import

## Usage

### Basic Usage

```python
from app.agent import create_agent

# Create agent instance
agent = create_agent(
    api_key="your-openai-key",
    model="gpt-4-turbo-preview"
)

# Process user message
response = await agent.process_message(
    "I need help understanding the cardiovascular system"
)

print(response)
```

### Streaming Responses

```python
async for chunk in agent.stream_message(user_message):
    print(chunk, end="", flush=True)
```

### Accessing Tools Directly

```python
from app.agent import execute_tool

# Get weak topics
weak_topics = execute_tool("get_weak_topics", {"threshold": 0.3})

# Generate quiz
quiz = execute_tool("generate_quiz", {
    "topic_id": "cardiology_basics",
    "num_questions": 5,
    "difficulty": "medium"
})
```

### Custom Prompts

```python
from app.agent import get_prompt_manager

pm = get_prompt_manager()

# Get formatted prompt
quiz_prompt = pm.format_prompt(
    "quiz_generation",
    topic_name="Hypertension",
    num_questions=5,
    difficulty="hard",
    confidence=0.6
)
```

## Key Features

### 1. Data-Driven Learning
- Grounds all recommendations in actual student data
- Checks confidence scores, prerequisites, and study history
- Identifies knowledge gaps proactively

### 2. Spaced Repetition
- Integrates forgetting curve into recommendations
- Tracks when topics need review
- Prevents knowledge decay

### 3. UK Medical Context
- References NICE guidelines, BNF, GMC outcomes
- Uses UK terminology and resources
- Aligned with UK medical school curriculum

### 4. Knowledge Graph Integration
- Understands topic dependencies
- Ensures prerequisites are mastered first
- Shows learning pathways

### 5. Personalized Study Plans
- Generates plans based on exams and weak areas
- Balances active and passive learning
- Realistic time allocation

### 6. Active Learning
- Generates custom quizzes
- Tracks performance over time
- Promotes recall over recognition

## Prompt Engineering

### System Prompt Structure

The main system prompt (`tutor_system.txt`) defines:

1. **Identity**: Aetios, expert medical tutor for UK students
2. **Capabilities**: 17 tools and knowledge graph access
3. **Responsibilities**: 
   - Proactive gap identification
   - Data-grounded responses
   - Spaced repetition awareness
   - UK medical context
   - Exam preparation
   - Active learning promotion
4. **Communication Style**: Conversational, supportive, structured
5. **Tool Usage Patterns**: When and how to use each tool
6. **Key Principles**: Prerequisites first, data-driven, etc.

### Quiz Generation Prompt

Provides detailed guidelines for:
- Difficulty levels (easy/medium/hard)
- Question quality standards
- UK medical focus areas
- Question types and structure
- Adaptive difficulty based on confidence

### Study Plan Prompt

Covers:
- Spaced repetition integration
- Prerequisite-first approach
- Balanced coverage
- Exam-driven prioritization
- Active learning methods
- UK-specific resources
- Daily study block structure

## Integration with Backend

The agent system integrates with the FastAPI backend:

```python
# In routers/agent.py
from app.agent import create_agent

agent = create_agent()

@router.post("/chat")
async def chat(message: str):
    response = await agent.process_message(message)
    return {"response": response}
```

## Testing

Run component tests:

```bash
cd backend
python -m pytest tests/test_agent/
```

Test individual components:

```python
# Test tools
from app.agent import TOOL_DEFINITIONS
assert len(TOOL_DEFINITIONS) == 18  # All 18 tools as specified

# Test prompts
from app.agent import get_system_prompt
prompt = get_system_prompt()
assert "Aetios" in prompt

# Test orchestrator
from app.agent import create_agent
agent = create_agent()
assert agent.model == "gpt-4-turbo-preview"
```

## Future Enhancements

1. **Database Integration**: Connect tools to actual student database
2. **Real-time Updates**: WebSocket support for streaming
3. **Multi-modal**: Support images (diagrams, X-rays, ECGs)
4. **Voice Interface**: Audio input/output for hands-free learning
5. **Collaborative Learning**: Group study features
6. **Advanced Analytics**: Learning pattern analysis
7. **Mobile Optimization**: Native app integration

## References

- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- UK Medical Education: GMC Outcomes for Graduates
- Spaced Repetition: Ebbinghaus forgetting curve
- Active Learning: Retrieval practice research

---

**Named after**: Aetius of Amida (6th century Byzantine physician)
**Purpose**: Democratize medical education through AI-powered personalization
**Context**: UK medical school curriculum and NHS clinical practice
