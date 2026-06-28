# Game Product Ops AI

## Vision

Game Product Ops AI is an autonomous AI Product Operations Agent built for Game Product Managers.

It automates the repetitive investigative work performed before product decisions are made.

Instead of manually checking telemetry dashboards, player reviews, patch notes, crash reports, LiveOps metrics, and other internal systems, the PM provides a business objective. The AI autonomously investigates, gathers evidence across multiple sources, correlates findings, identifies root causes, and prepares decision-ready artifacts.

The PM remains the decision maker.

The AI performs the investigation.

---

# Problem Statement

Modern Product Managers spend a significant amount of time gathering information from disconnected systems before they can make informed decisions.

Typical workflow:

Telemetry

↓

Player Reviews

↓

Patch Notes

↓

Crash Reports

↓

LiveOps

↓

Analytics

↓

Product Decision

This repetitive context switching is manual, slow, and difficult to scale.

The goal of this project is to automate the investigation, not the decision.

---

# Product Philosophy

This project is NOT:

- An AI chatbot
- A ChatGPT clone
- An analytics dashboard with AI summaries
- A generic LLM wrapper

This project IS:

- An autonomous Product Operations Agent
- A goal-driven investigation system
- An AI employee that performs product analysis before the PM reviews the results

Every feature should reinforce this philosophy.

---

# Primary Users

Primary

- Game Product Managers

Secondary

- Product Analysts
- LiveOps Managers
- Game Designers
- Producers

---

# Core User Flow

The PM provides a business objective.

Examples:

- Why is retention dropping?
- Why are Ranked players leaving?
- Evaluate Patch 1.3.
- Analyze weekend LiveOps.
- Investigate revenue decline.

The AI should then:

1. Understand the objective.
2. Plan the investigation.
3. Decide which tools are required.
4. Gather relevant evidence.
5. Correlate findings.
6. Identify likely root causes.
7. Prioritize issues.
8. Recommend actions.
9. Generate decision-ready artifacts.
10. Wait for human approval.

---

# AI Principles

The AI should feel proactive.

Not reactive.

The AI should:

- Plan investigations.
- Choose relevant tools.
- Collect evidence.
- Correlate information.
- Explain findings.
- Recommend actions.

The AI should never require the PM to manually specify which data sources to inspect.

---

# Investigation Workflow

Business Objective

↓

Planning

↓

Tool Selection

↓

Evidence Collection

↓

Evidence Correlation

↓

Root Cause Analysis

↓

Recommendations

↓

Decision Artifacts

---

# Data Sources

All data is synthetic but realistic.

Supported sources:

- Gameplay telemetry
- Player reviews
- Patch notes
- Crash reports
- LiveOps events
- Revenue metrics
- Store purchases
- Session analytics

No external APIs are required for the MVP.

---

# Investigation Tools

The AI has access to internal investigation tools.

Examples:

- getTelemetry()
- searchReviews()
- readPatchNotes()
- getCrashMetrics()
- getRevenueMetrics()
- getLiveOpsEvents()

The AI determines which tools are required.

Different objectives should trigger different investigation workflows.

---

# Decision Artifacts

Every completed investigation should produce:

- Executive Brief
- Root Cause Analysis
- Evidence Board
- Prioritized Issues
- Recommendations
- Suggested A/B Tests
- Risk Assessment

---

# Evidence First

Every recommendation must be backed by evidence.

Example:

Recommendation

Rollback MMR Update

Evidence

✓ Retention decreased 12%

✓ Reviews mention matchmaking

✓ Patch modified MMR

Confidence

91%

The AI should never generate unsupported recommendations.

---

# Design Principles

Every feature should satisfy these principles.

1. AI performs work rather than conversations.
2. Objectives drive investigations.
3. Recommendations require evidence.
4. Human approval is always required.
5. Different objectives produce different investigation workflows.
6. The interface visualizes AI activity.
7. Automation is more important than feature count.

---

# Engineering Priorities

When choosing between multiple implementations, prioritize:

1. AI autonomy
2. Product workflow realism
3. Clean architecture
4. Extensibility
5. User experience
6. Visual polish
7. Performance

Never sacrifice AI autonomy for unnecessary features.

---

# Definition of Success

A successful investigation requires only a business objective from the user.

The AI independently:

- Determines what information is needed.
- Chooses the appropriate investigation tools.
- Collects evidence.
- Correlates findings.
- Generates recommendations.
- Produces decision-ready artifacts.

The PM never manually instructs the AI which systems to inspect.

---

# MVP Scope

Build one polished investigation workflow.

Include:

- Dashboard
- Objective input
- Investigation timeline
- Evidence Board
- Executive Brief
- Recommendations
- Decision artifacts

Avoid partially completed modules.

---

# Technical Goals

- Modular architecture
- Provider-independent LLM layer
- Maintainable code
- Easy future expansion
- Professional internal-tool quality

---

# Non Goals

Do not build:

- Authentication
- Multiplayer
- External integrations
- Production infrastructure
- Live telemetry ingestion
- Complex multi-agent frameworks

Everything runs locally using realistic synthetic data.

---

# Anti Goals

The project should never become:

- A generic chatbot
- A ChatGPT clone
- A summarization tool
- A static analytics dashboard
- An AI that recommends actions without evidence

---

# Future Roadmap

Possible future modules:

- Decision memory
- Weekly reports
- Economy balancing
- Patch simulator
- Feature prioritization
- Sprint planning
- Jira integration
- Slack integration
- Multi-agent collaboration

These are intentionally outside the MVP.

---

# Success Criteria

When someone opens the application, they should immediately think:

"This AI performs Product Operations."

Not:

"This is another AI summarizer."

Every implementation decision should move the product toward autonomous investigation rather than conversational AI.