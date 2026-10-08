"""Prompt templates used for quiz generation."""


QUIZ_PROMPT_TEMPLATE = """
Based on the following transcript, generate a quiz in valid JSON format.
The quiz must follow this exact structure:
{
  "title": "Create a concise quiz title based on the topic of the transcript.",
  "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
  "questions": [
    {
      "question_title": "The question goes here.",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct answer from the above options"
    }
  ]
}
Requirements:
- Generate exactly 10 questions.
- Each question must have exactly 4 distinct answer options.
- Only one correct answer is allowed per question.
- The correct answer must be present in "question_options".
- The output must be valid JSON and parsable with json.loads.
- Do not include explanations, comments, or text outside the JSON.
"""
