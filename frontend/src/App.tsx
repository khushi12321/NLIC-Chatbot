
import { useEffect, useState } from 'react'
import { checkBackendHealth } from './services/api'

function App() {
  const [status, setStatus] = useState('Checking backend...')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    checkBackendHealth()
      .then((data) => setStatus(data.message))
      .catch((err: unknown) => {
        setError(
          err instanceof Error ? err.message : 'Something went wrong',
        )
      })
  }, [])

  return (
    <main>
      <h1>NLIC Chatbot</h1>
      {error ? (
        <p>Connection failed: {error}</p>
      ) : (
        <p>{status}</p>
      )}
    </main>
  )
}

export default App
