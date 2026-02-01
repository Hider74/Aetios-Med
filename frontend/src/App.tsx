import React, { useState } from 'react'
import Sidebar from './components/common/Sidebar'
import TopBar from './components/common/TopBar'
import Dashboard from './components/Dashboard/Dashboard'
import KnowledgeGraphView from './components/KnowledgeGraph/GraphCanvas'
import ChatInterface from './components/Chat/ChatInterface'
import StudyPlanView from './components/StudyPlan/PlanGenerator'

type View = 'dashboard' | 'graph' | 'chat' | 'study';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard')

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />
      case 'graph':
        return <KnowledgeGraphView />
      case 'chat':
        return <ChatInterface />
      case 'study':
        return <StudyPlanView />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar currentView={currentView} onViewChange={setCurrentView} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-auto">
          {renderView()}
        </main>
      </div>
    </div>
  )
}

export default App
