"use client"

import { Bot } from 'lucide-react'

export default function AskAIPage() {
  return (
    <div className="min-h-screen bg-gray-50 px-6 py-8">
      <div className="max-w-lg mx-auto">
        <h1 className="text-2xl font-bold mb-2">Ask AI</h1>
        <p className="text-gray-600 mb-12">
          Get personalized workout advice and answers to your fitness questions
        </p>

        <div className="bg-white rounded-lg p-8 text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
              <Bot className="w-8 h-8 text-gray-400" />
            </div>
          </div>

          <h2 className="text-xl font-semibold mb-4">AI Assistant Coming Soon</h2>
          <p className="text-gray-600 leading-relaxed">
            This feature will help you with workout planning, exercise form tips, and personalized fitness advice.
          </p>
        </div>
      </div>
    </div>
  )
}
