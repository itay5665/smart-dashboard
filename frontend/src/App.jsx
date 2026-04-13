import { useEffect, useState } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = 'https://smart-dashboard-backend-dilq.onrender.com'

function App() {
  const [tasks, setTasks] = useState([])
  const [newTitle, setNewTitle] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [aiSummary, setAiSummary] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState('')

  // Load all tasks from the backend when the page first opens.
  const fetchTasks = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await axios.get(`${API_URL}/tasks`)
      setTasks(response.data)
    } catch (fetchError) {
      setError('Could not load tasks. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  // Send a new task title to the backend and refresh the list.
  const handleAddTask = async () => {
    const trimmedTitle = newTitle.trim()
    if (!trimmedTitle) return

    try {
      setError('')
      await axios.post(`${API_URL}/tasks`, { title: trimmedTitle })
      setNewTitle('')
      await fetchTasks()
    } catch (addError) {
      setError('Failed to add task.')
    }
  }

  // Toggle one task between completed and not completed.
  const handleToggleTask = async (taskId) => {
    try {
      setError('')
      await axios.put(`${API_URL}/tasks/${taskId}`)
      await fetchTasks()
    } catch (toggleError) {
      setError('Failed to update task.')
    }
  }

  // Remove one task from the backend by its id.
  const handleDeleteTask = async (taskId) => {
    try {
      setError('')
      await axios.delete(`${API_URL}/tasks/${taskId}`)
      await fetchTasks()
    } catch (deleteError) {
      setError('Failed to delete task.')
    }
  }

  // Request an AI analysis of current tasks from the backend.
  const handleAiSummary = async () => {
    try {
      setAiLoading(true)
      setAiError('')
      const response = await axios.post(`${API_URL}/summarize`)
      // Backend now returns { summary: "..." }, so prefer that key.
      setAiSummary(
        response.data.summary ||
          response.data.analysis ||
          'No summary returned by the AI.'
      )
    } catch (summaryError) {
      setAiError('Failed to generate AI summary. Please try again.')
    } finally {
      setAiLoading(false)
    }
  }

  // Trigger the first data load when this component mounts.
  useEffect(() => {
    fetchTasks()
  }, [])

  return (
    <main className="dashboard">
      <section className="panel">
        <header className="panel-header">
          <h1>Task Dashboard</h1>
          <p>Plan, track, and complete your tasks.</p>
        </header>

        <div className="add-task-row">
          <input
            type="text"
            value={newTitle}
            onChange={(event) => setNewTitle(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                handleAddTask()
              }
            }}
            placeholder="Enter a new task..."
            aria-label="New task title"
          />
          <button className="primary-btn" onClick={handleAddTask}>
            Add Task
          </button>
        </div>

        {error && <p className="error-text">{error}</p>}

        <div className="ai-summary-section">
          <button
            className="ai-btn"
            onClick={handleAiSummary}
            disabled={aiLoading}
          >
            AI Summary
          </button>
          {aiLoading && <p className="status-text">Analyzing your tasks...</p>}
          {aiError && <p className="error-text">{aiError}</p>}
          {aiSummary && !aiLoading && (
            <article className="ai-summary-card">
              <h2>Claude Analysis</h2>
              <p>{aiSummary}</p>
            </article>
          )}
        </div>

        <div className="task-list-wrapper">
          {loading ? (
            <p className="status-text">Loading tasks...</p>
          ) : tasks.length === 0 ? (
            <p className="status-text">No tasks yet. Add your first one.</p>
          ) : (
            <ul className="task-list">
              {tasks.map((task) => (
                <li key={task.id} className="task-item">
                  <span className={task.done ? 'task-title done' : 'task-title'}>
                    {task.title}
                  </span>
                  <div className="task-actions">
                    <button
                      className="secondary-btn"
                      onClick={() => handleToggleTask(task.id)}
                    >
                      {task.done ? 'Mark Undone' : 'Mark Done'}
                    </button>
                    <button
                      className="danger-btn"
                      onClick={() => handleDeleteTask(task.id)}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </main>
  )
}

export default App
