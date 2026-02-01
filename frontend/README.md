# Aetios-Med Frontend

React + TypeScript frontend for Aetios-Med, an offline-first medical study assistant with a living knowledge graph.

## 🏗️ Architecture

### Directory Structure

```
src/
├── types/              # TypeScript type definitions
│   ├── curriculum.ts   # Knowledge graph types
│   ├── chat.ts        # Chat and quiz types
│   └── study.ts       # Study plan and exam types
│
├── services/          # External service integrations
│   ├── api.ts        # FastAPI backend client (Axios)
│   └── ipc.ts        # Electron IPC wrapper
│
├── stores/            # Zustand state management
│   ├── graphStore.ts      # Knowledge graph state
│   ├── chatStore.ts       # Chat session state
│   └── settingsStore.ts   # App settings
│
├── hooks/             # Custom React hooks
│   ├── useGraph.ts         # Graph operations
│   ├── useChat.ts          # Chat operations
│   ├── useStudySession.ts  # Study tracking
│   └── useModelStatus.ts   # Model download status
│
└── components/        # React components
    ├── common/            # Reusable UI components
    ├── Dashboard/         # Main overview
    ├── KnowledgeGraph/    # Interactive graph visualization
    ├── Chat/              # AI tutor interface
    ├── StudyPlan/         # Study planning tools
    ├── Setup/             # First-run setup wizard
    └── ResourceViewer/    # In-app browser
```

## 🎨 Component Overview

### Common Components
- **Sidebar**: Navigation with collapsible menu
- **TopBar**: Page title and status indicators
- **LoadingSpinner**: Loading states

### Dashboard
- **Dashboard**: Main overview with quick actions
- **ConfidenceOverview**: Stats cards for progress
- **UpcomingExams**: Exam list with priorities
- **DecayingTopics**: Topics needing review

### Knowledge Graph
- **GraphCanvas**: Cytoscape.js visualization with confidence colors
  - Red (≤30%): Low confidence
  - Amber (30-60%): Medium confidence
  - Green (>60%): High confidence
- **GraphControls**: Zoom, filter, layout, search
- **NodeDetail**: Side panel with topic details

### Chat Interface
- **ChatInterface**: Main chat UI with AI tutor
- **MessageBubble**: Formatted chat messages
- **QuizCard**: Interactive quiz questions

### Study Plan
- **PlanGenerator**: AI-powered study plan generation
- **CalendarView**: Visual calendar with tasks
- **ExportICS**: Export to calendar apps

### Setup Wizard
- **ModelDownload**: Download AI models with progress
- **HuggingFaceAuth**: Optional token configuration
- **FolderConfig**: Select resource folders

### Resource Viewer
- **WebViewPanel**: In-app browser for medical resources

## 🔧 State Management

### Zustand Stores

**graphStore**
- Knowledge graph data
- Node selection
- Filters and layout
- CRUD operations on nodes

**chatStore**
- Chat sessions
- Message history
- Context management
- Quiz state

**settingsStore**
- User preferences
- Theme (light/dark)
- Resource folders
- Model configuration

## 🎯 Key Features

### Offline-First
- Works without internet after setup
- Local model execution
- Persisted state with Zustand persist middleware

### Responsive Design
- TailwindCSS for styling
- Dark mode support
- Mobile-friendly layouts

### Type Safety
- Full TypeScript coverage
- Strict mode enabled
- Comprehensive type definitions

### Error Handling
- Try-catch blocks in all async operations
- User-friendly error messages
- Graceful fallbacks

## 📦 Dependencies

### Core
- React 18.2.0
- TypeScript 5.3.3
- Vite 5.0.11

### UI & Styling
- TailwindCSS 3.4.1
- lucide-react 0.312.0 (icons)
- date-fns 3.2.0 (date formatting)

### Data & State
- Zustand 4.5.0 (state management)
- Axios 1.6.5 (HTTP client)

### Graph Visualization
- Cytoscape.js 3.28.1
- cytoscape-cola 2.5.1 (force-directed layout)
- cytoscape-dagre 2.5.0 (hierarchical layout)

## 🚀 Getting Started

### Development
```bash
npm run dev
```

### Build
```bash
npm run build
```

### Type Check
```bash
npm run type-check
```

### Lint
```bash
npm run lint
```

## 🎨 Design Principles

### Color System
- **Blue**: Primary actions, navigation
- **Green**: Success, high confidence
- **Yellow/Amber**: Medium confidence, warnings
- **Red**: Low confidence, critical items
- **Purple**: AI features, chat

### Confidence Visualization
- Graph nodes colored by confidence level
- Progress bars for topic mastery
- Visual urgency indicators

### User Experience
- Instant feedback on actions
- Loading states for async operations
- Keyboard shortcuts where applicable
- Accessible (ARIA labels)

## 🔗 API Integration

The frontend communicates with the FastAPI backend on `localhost:8741`:

- **GET** `/api/graph` - Fetch knowledge graph
- **POST** `/api/chat` - Send chat message
- **POST** `/api/study/plan/generate` - Generate study plan
- **GET** `/api/exams` - Get exam list
- **POST** `/api/quiz/generate` - Generate quiz questions

## 🔐 Security

- No credentials stored in localStorage
- IPC communication for Electron features
- Sandboxed iframes for external content
- Input validation on all forms

## 📝 Future Enhancements

- [ ] Real-time collaboration
- [ ] Advanced graph analytics
- [ ] Spaced repetition algorithm
- [ ] Voice input for chat
- [ ] Mobile app (React Native)
- [ ] Plugin system

## 🤝 Contributing

1. Follow existing code style
2. Add TypeScript types for new features
3. Include error handling
4. Update this README for major changes

## 📄 License

MIT - See LICENSE file in root directory
