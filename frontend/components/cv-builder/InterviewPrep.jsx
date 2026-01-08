/**
 * AI Interview Preparation Component
 * Generate questions and practice answers
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Sparkles, CheckCircle, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";

export default function InterviewPrep({ cvData }) {
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState(null);
  const [currentCategory, setCurrentCategory] = useState("behavioral");
  const [userAnswers, setUserAnswers] = useState({});
  const [showFeedback, setShowFeedback] = useState({});

  const handleGenerateQuestions = async () => {
    if (!jobDescription.trim()) {
      toast.error("Please enter a job description");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://192.168.100.93:8000"}/api/cv/generate-interview-questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cv_data: cvData,
          job_description: jobDescription,
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        setQuestions(result.questions);
        toast.success("Interview questions generated!");
      } else {
        toast.error("Failed to generate questions");
      }
    } catch (error) {
      toast.error("Error generating questions");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = (questionId, answer) => {
    setUserAnswers(prev => ({ ...prev, [questionId]: answer }));
    setShowFeedback(prev => ({ ...prev, [questionId]: true }));
  };

  const categories = questions ? Object.keys(questions) : [];

  return (
    <div className="card">
      <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <MessageSquare className="w-6 h-6" />
        AI Interview Preparation
      </h2>

      {/* Input */}
      {!questions && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-bold text-blue-900 mb-2">
              Job Description
            </label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              className="input-field min-h-[200px]"
              placeholder="Paste the job description to generate relevant interview questions..."
            />
          </div>
          <button
            onClick={handleGenerateQuestions}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            {loading ? "Generating Questions..." : "Generate Interview Questions"}
          </button>
        </div>
      )}

      {/* Questions Display */}
      {questions && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Category Tabs */}
          <div className="flex gap-2 border-b border-gray-200">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setCurrentCategory(category)}
                className={`px-4 py-2 font-semibold transition-colors ${
                  currentCategory === category
                    ? "text-blue-600 border-b-2 border-blue-600"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)} ({questions[category]?.length || 0})
              </button>
            ))}
          </div>

          {/* Questions List */}
          <div className="space-y-4">
            {questions[currentCategory]?.map((q, idx) => {
              const questionId = `${currentCategory}-${idx}`;
              const userAnswer = userAnswers[questionId];
              const showModelAnswer = showFeedback[questionId];

              return (
                <div
                  key={idx}
                  className="border border-gray-200 rounded-lg p-4 bg-white"
                >
                  <div className="flex items-start gap-3 mb-3">
                    <span className="bg-blue-100 text-blue-800 rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm flex-shrink-0">
                      {idx + 1}
                    </span>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">
                        {q.question}
                      </h4>
                      
                      {/* User Answer Input */}
                      {!userAnswer && (
                        <div className="space-y-2">
                          <textarea
                            placeholder="Type your answer here..."
                            className="input-field min-h-[100px] text-sm"
                            onBlur={(e) => {
                              if (e.target.value.trim()) {
                                handleAnswerSubmit(questionId, e.target.value);
                              }
                            }}
                          />
                          <button
                            onClick={(e) => {
                              const textarea = e.target.previousElementSibling;
                              if (textarea.value.trim()) {
                                handleAnswerSubmit(questionId, textarea.value);
                              }
                            }}
                            className="btn-secondary text-sm"
                          >
                            Submit Answer
                          </button>
                        </div>
                      )}

                      {/* User Answer Display */}
                      {userAnswer && (
                        <div className="mb-3">
                          <p className="text-sm font-semibold text-gray-700 mb-1">Your Answer:</p>
                          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-gray-800">
                            {userAnswer}
                          </div>
                        </div>
                      )}

                      {/* Model Answer */}
                      {showModelAnswer && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          className="mt-3"
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <CheckCircle className="w-4 h-4 text-green-600" />
                            <p className="text-sm font-semibold text-gray-700">Model Answer:</p>
                          </div>
                          <div className="bg-green-50 border border-green-200 rounded p-3 text-sm text-gray-800">
                            {q.model_answer}
                          </div>
                          {q.key_points && q.key_points.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-semibold text-gray-600 mb-1">Key Points:</p>
                              <ul className="list-disc list-inside text-xs text-gray-700 space-y-1">
                                {q.key_points.map((point, pIdx) => (
                                  <li key={pIdx}>{point}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <button
            onClick={() => {
              setQuestions(null);
              setJobDescription("");
              setUserAnswers({});
              setShowFeedback({});
            }}
            className="btn-secondary w-full"
          >
            Generate New Questions
          </button>
        </motion.div>
      )}
    </div>
  );
}

