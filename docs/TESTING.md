# LangGraph Patterns — Testing Guide

Realistic prompts to quickly validate each agent pattern via the Local UI Test tab or LangGraph Studio Chat.

Notes
- Use input shape: `{ "messages": [{"role":"human","content":"..."}] }`
- Replace `...` with the suggested prompts below.

## example
- "Summarize the key benefits of containerizing ML inference services."

## prompt_chaining
- "Write a 3-section blog post about adopting feature stores in a fintech startup. Keep it actionable."
- "Create an outline and a short draft for a workshop on introduction to Kubernetes for data scientists."

## routing
- "Compare Rust and Go for building high-performance APIs."
- "What are early signs of burnout and how can tech teams mitigate them? (not medical advice)"
- "Explain the difference between ETFs and mutual funds for a beginner. (not financial advice)"

## parallel_sectioning (story + joke + poem)
- "Use the topic: migrating a monolith to microservices with zero downtime."
- "Topic: designing a robust feature engineering pipeline for churn prediction."

## parallel_voting (generate 3 taglines and pick the best)
- "Create product taglines for a privacy-first analytics platform for SaaS startups."
- "Propose 3 conference titles for a talk about GenAI guardrails in production."

## orchestrator_worker
- "Plan and produce content for a 2-week launch campaign of a developer tool (docs improvements, blog, tweets)."
- "Given the task 'audit the reliability of our nightly training pipeline', break it down and deliver concise findings."

## evaluator_optimizer
- "Draft a professional email to a customer explaining an incident, then improve it based on a brief critique."
- "Write a short FAQ for engineers onboarding to the platform team; make it clearer after critique."

## tool_agent (calculator)
- "Compute: (42 * 7 - 13) / 5"
- "What is 3.5% of 12500 plus 299?"
