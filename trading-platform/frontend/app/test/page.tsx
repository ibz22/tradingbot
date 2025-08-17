'use client'

export default function TestPage() {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto">
        <div className="card">
          <h1 className="text-2xl font-bold text-text-primary mb-4">
            🚀 Solsak Trading Platform Test
          </h1>
          
          <div className="space-y-4">
            <div className="p-4 bg-success/20 text-success rounded-lg">
              ✅ Frontend is working correctly!
            </div>
            
            <div className="p-4 bg-primary/20 text-primary rounded-lg">
              🎨 Tailwind CSS is configured properly
            </div>
            
            <div className="p-4 bg-card border border-border rounded-lg">
              <h2 className="font-semibold text-text-primary mb-2">Next Steps:</h2>
              <ol className="list-decimal list-inside text-text-secondary space-y-1">
                <li>Start the backend server: <code className="bg-background px-2 py-1 rounded">python backend/main.py</code></li>
                <li>Go to the main dashboard: <a href="/" className="text-primary hover:underline">http://localhost:3000</a></li>
                <li>Create your first trading bot</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}