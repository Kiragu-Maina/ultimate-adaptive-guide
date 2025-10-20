# Getting Started with AlkenaCode

This guide will walk you through setting up and using the AlkenaCode Adaptive Learning Platform from scratch.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [First-Time Setup](#first-time-setup)
- [Your First Learning Journey](#your-first-learning-journey)
- [Understanding the Dashboard](#understanding-the-dashboard)
- [Taking Your First Quiz](#taking-your-first-quiz)
- [Tracking Your Progress](#tracking-your-progress)
- [Next Steps](#next-steps)

---

## Prerequisites

### Required Software

1. **Docker Desktop** (version 20.10+)
   - **macOS**: [Download Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - **Windows**: [Download Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - **Linux**: [Install Docker Engine](https://docs.docker.com/engine/install/)

2. **Docker Compose** (version 2.0+)
   - Included with Docker Desktop (Mac/Windows)
   - Linux: Install separately via package manager

3. **Git**
   - **macOS**: Pre-installed or via Homebrew: `brew install git`
   - **Windows**: [Download Git for Windows](https://git-scm.com/download/win)
   - **Linux**: `sudo apt install git` (Ubuntu/Debian) or equivalent

### Required API Key

4. **OpenRouter API Key**
   - Sign up at [openrouter.ai](https://openrouter.ai/)
   - Navigate to "API Keys" in your account
   - Create a new API key
   - Copy the key (starts with `sk-or-v1-...`)
   - **Cost**: Free tier available with rate limits

### System Requirements

- **Operating System**: macOS, Windows 10/11, or Linux
- **RAM**: Minimum 4GB, recommended 8GB
- **Disk Space**: At least 5GB free
- **Network**: Stable internet connection
- **Browser**: Modern browser (Chrome, Firefox, Safari, Edge)

---

## Installation

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/alkenacode-adaptive-learning.git

# Navigate to project directory
cd alkenacode-adaptive-learning

# Verify files
ls -la
# Should see: multiagential/, docs/, README.md, LICENSE, etc.
```

### Step 2: Configure Environment Variables

```bash
# Navigate to backend directory
cd multiagential/backend

# Create .env file
cat > .env << 'EOF'
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Database Configuration
DATABASE_URL=postgresql://adaptive_user:adaptive_pass@postgres:5432/adaptive_learning

# Redis Configuration
REDIS_URL=redis://redis:6379

# Optional: Model Configuration
DEFAULT_MODEL=openai/gpt-oss-120b
FALLBACK_MODELS=nousresearch/deephermes-3-mistral-24b-preview,google/gemini-2.5-flash-lite
EOF

# Edit the file to add your actual API key
nano .env
# or
vim .env
```

**Important**: Replace `your_openrouter_api_key_here` with your actual OpenRouter API key.

### Step 3: Verify Docker Installation

```bash
# Check Docker version
docker --version
# Expected: Docker version 20.10.0 or higher

# Check Docker Compose version
docker compose version
# Expected: Docker Compose version v2.0.0 or higher

# Test Docker is running
docker ps
# Should return: CONTAINER ID   IMAGE   ... (empty list is fine)
```

If Docker commands fail:
- **Mac/Windows**: Open Docker Desktop application
- **Linux**: Start Docker service: `sudo systemctl start docker`

---

## First-Time Setup

### Step 1: Build and Start Services

```bash
# Navigate to multiagential directory
cd /path/to/alkenacode-adaptive-learning/multiagential

# Build and start all services
docker compose up --build -d
```

**What happens**:
1. Downloads PostgreSQL 16 Alpine image (~80MB)
2. Downloads Redis 7 Alpine image (~40MB)
3. Builds backend Python image (~500MB)
4. Builds frontend Next.js image (~400MB)
5. Creates Docker volumes for data persistence
6. Starts all 4 services with health checks

**Expected output**:
```
[+] Building 120.3s (45/45) FINISHED
[+] Running 6/6
 ✔ Network multiagential_default         Created
 ✔ Volume "multiagential_postgres_data"  Created
 ✔ Volume "multiagential_redis_data"     Created
 ✔ Container multiagential-postgres-1    Healthy
 ✔ Container multiagential-redis-1       Healthy
 ✔ Container multiagential-backend-1     Started
 ✔ Container multiagential-frontend-1    Started
```

**Time**: 2-5 minutes (first time, depending on internet speed)

### Step 2: Verify Services Are Running

```bash
# Check service status
docker compose ps
```

**Expected output**:
```
NAME                        STATUS         PORTS
multiagential-backend-1     Up (healthy)   0.0.0.0:8007->8000/tcp
multiagential-frontend-1    Up             0.0.0.0:3007->3000/tcp
multiagential-postgres-1    Up (healthy)   5432/tcp
multiagential-redis-1       Up (healthy)   6379/tcp
```

All services should show `Up` or `Up (healthy)`.

### Step 3: Initialize Database

The database is automatically initialized on first backend startup. Verify:

```bash
# Check database initialization logs
docker compose logs backend | grep "Database initialized"

# Should see: ✅ Database initialized with all tables
```

If not initialized, run manually:

```bash
docker compose exec backend python init_db.py
```

### Step 4: Verify System Health

```bash
# Test backend API
curl http://localhost:4465/

# Expected response:
# {
#   "status": "ok",
#   "adaptive_agents": "online",
#   "agents_count": 8,
#   "redis": "healthy",
#   "cache_available": true,
#   "postgres": "connected"
# }
```

### Step 5: Access the Frontend

Open your browser and navigate to:

```
http://localhost:4464
```

You should see the AlkenaCode dashboard with:
- Navigation bar (Dashboard, Courses, Quiz, Content, Feedback)
- Welcome message: "Hey there! Ready to learn?"
- Purple banner: "Experience True Adaptive Learning"
- 4 quick action cards

**If you see this, setup is complete!** ✅

---

## Your First Learning Journey

### Step 1: Start Onboarding

1. Click the **"🚀 Start Your Adaptive Journey"** button on the dashboard
2. You'll be redirected to `/adaptive` page
3. The onboarding modal will automatically open

### Step 2: Complete Onboarding (4 Steps)

#### **Step 1: Select Your Interests**

- **What you'll see**: Grid of interest cards with icons
- **Available interests**:
  - Python Programming
  - Web Development
  - Data Science
  - Machine Learning
  - Mobile Development
  - Cloud Computing
  - Cybersecurity
  - DevOps

**Example selection**: Click "Python Programming" and "Web Development"

#### **Step 2: Choose Your Goals**

- **What you'll see**: Checkboxes for learning goals
- **Available goals**:
  - Career Change
  - Skill Upgrade
  - Personal Project
  - Academic Requirements
  - Interview Preparation
  - Certification

**Example selection**: Check "Career Change" and "Skill Upgrade"

#### **Step 3: Set Your Preferences**

**Time Commitment**:
- Slider from 1-20 hours per week
- **Example**: Set to 10 hours/week

**Learning Style**:
- Visual (diagrams, videos, infographics)
- Reading (text, articles, documentation)
- Interactive (quizzes, exercises, projects)
- Mixed (combination of all)

**Example**: Select "Visual" or "Mixed"

**Skill Level**:
- Beginner (new to the topic)
- Intermediate (some experience)
- Advanced (experienced, looking to deepen)

**Example**: Select "Beginner"

#### **Step 4: Review and Submit**

- Review all your selections
- Click **"🚀 Start My Learning Journey"**
- Watch AI agents work in real-time!

### Step 3: Watch AI Agents Work

**What happens** (~2 minutes):

1. **Learner Profiler Agent** (45 seconds)
   - Status: "🔍 Analyzing your interests and skill level..."
   - Progress bar fills up
   - Completion: "✅ Profile created with 95% confidence"

2. **Journey Architect Agent** (75 seconds)
   - Status: "🏗️ Designing your personalized learning path..."
   - Shows DuckDuckGo API calls for topic discovery
   - Progress bar fills up
   - Completion: "✅ Journey designed with 9 topics"

**Visual feedback**:
```
🤖 AI Agents Working...

✅ Learner Profiler
   Created comprehensive learner profile
   Confidence: 95%

🔄 Journey Architect
   Designing personalized learning journey...
   Progress: [████████░░] 80%
```

### Step 4: View Your Personalized Dashboard

Once complete, you'll see:

1. **Profile Summary**
   ```
   📊 Your Learning Profile

   Overall Skill Level: Beginner
   Primary Interests: Python Programming, Web Development
   Learning Style: Visual
   Time Commitment: 10 hours/week

   Created by Learner Profiler Agent
   ```

2. **Learning Journey** (9-50 topics)
   ```
   🗺️ Your Learning Journey

   1. ✅ Python Installation and Setup (Available)
      ⏱️ 2 hours | 📚 Prerequisites: None
      [Start Learning →]

   2. 🔒 Basic Syntax and Variables (Locked)
      ⏱️ 5 hours | 📚 Prerequisites: Python Installation

   3. 🔒 Control Structures (Locked)
      ⏱️ 8 hours | 📚 Prerequisites: Basic Syntax

   ...

   5. ⭐ Object-Oriented Programming Basics (Milestone)
      ⏱️ 10 hours | 📚 Prerequisites: Functions and Scope
   ```

3. **Smart Recommendations**
   ```
   🎯 Recommended Topics

   ➤ Python Installation and Setup
     Perfect starting point for beginners
     Score: 0.95 | Source: Journey

   ➤ Introduction to Programming Concepts
     Build foundational understanding
     Score: 0.88 | Source: Knowledge Gap
   ```

**Congratulations!** Your personalized learning journey is ready! 🎉

---

## Understanding the Dashboard

### Navigation Bar

```
┌────────────────────────────────────────────────────────┐
│ 🏫 AlkenaCode School        🤖 Adaptive Mode Active   │
├────────────────────────────────────────────────────────┤
│ Dashboard | 🤖 Adaptive • | Courses | Quiz | Content  │
└────────────────────────────────────────────────────────┘
```

- **Dashboard**: Main landing page
- **🤖 Adaptive Journey**: Your personalized learning path (green dot when active)
- **Courses**: Browse all available courses
- **Quiz**: Take quizzes on any topic
- **Content**: Access learning materials
- **Feedback**: Get motivational feedback
- **Progress**: View analytics and mastery charts

### Dashboard Sections

#### 1. Adaptive Learning Banner (Top)

**Before onboarding**:
```
╔══════════════════════════════════════════════╗
║ 🤖 Experience True Adaptive Learning         ║
║                                              ║
║ Let 8 AI agents collaborate to create       ║
║ your personalized learning journey           ║
║                                              ║
║ [🤖] [📊] [🎯] [📚] [✅] [🔍] [📈] [💪]    ║
║                                              ║
║ [🚀 Start Your Adaptive Journey]            ║
╚══════════════════════════════════════════════╝
```

**After onboarding**:
```
╔══════════════════════════════════════════════╗
║ ✅ Your Adaptive Journey is Ready!          ║
║                                              ║
║ Your personalized learning path is waiting  ║
║                                              ║
║ [Continue Learning →]                       ║
╚══════════════════════════════════════════════╝
```

#### 2. Profile Summary

Shows your learning profile created by the Learner Profiler Agent:
- Overall skill level
- Interests
- Goals
- Learning style
- Time commitment

#### 3. Learning Journey Map

Visual representation of your learning path:
- **Green cards**: Available (ready to start)
- **Blue cards**: In Progress (currently learning)
- **Gray cards**: Locked (prerequisites not met)
- **Checkmark**: Completed
- **⭐ Star**: Milestone (every 5 topics)

#### 4. Recommendations Section

Top 5 personalized topic suggestions from the Recommendation Agent:
- Composite relevance score
- Source (journey/gap/strength/exploration)
- Clear reasoning

#### 5. Progress Overview

Quick stats:
- Topics completed
- Quizzes taken
- Current streak
- Total learning hours

---

## Taking Your First Quiz

### Step 1: Navigate to a Topic

From your learning journey, click **"Start Learning"** on an available topic (e.g., "Python Installation and Setup").

### Step 2: Access Content

You'll see:
- **Learning Content**: Text, examples, exercises
- **Mermaid Diagrams**: Visual aids
- **Practice Questions**: Interactive exercises
- **Resources**: External links

### Step 3: Start a Quiz

Click **"Take Quiz"** button at the bottom of the content page.

### Step 4: Quiz Interface

```
┌─────────────────────────────────────────┐
│ Quiz: Python Installation and Setup     │
│ Difficulty: Medium (Adaptive)           │
│ Questions: 5                            │
├─────────────────────────────────────────┤
│ Question 1 of 5                         │
│                                         │
│ What is the recommended way to install  │
│ Python on Windows?                      │
│                                         │
│ ○ Download from python.org             │
│ ○ Use Windows Store                    │
│ ○ Install via Chocolatey               │
│ ○ All of the above                     │
│                                         │
│ [Next Question →]                      │
└─────────────────────────────────────────┘
```

**Features**:
- Progress bar showing question number
- Timer (optional, not enforced)
- Clear question text
- Multiple choice options
- Navigation buttons

### Step 5: Submit Quiz

After answering all questions, click **"Submit Quiz"**.

### Step 6: View Results

**Immediate feedback**:
```
┌─────────────────────────────────────────┐
│ 🎉 Quiz Complete!                       │
│                                         │
│ Score: 4/5 (80%)                       │
│                                         │
│ ✅ Question 1: Correct                 │
│ ✅ Question 2: Correct                 │
│ ❌ Question 3: Incorrect               │
│    Correct answer: B                    │
│ ✅ Question 4: Correct                 │
│ ✅ Question 5: Correct                 │
│                                         │
│ Mastery Updated:                        │
│ Python Installation: 78.5/100 ⬆️        │
│                                         │
│ 💪 Feedback:                           │
│ Great job! Your understanding is        │
│ improving. Ready for the next topic!    │
│                                         │
│ 🎯 Recommendations:                    │
│ • Basic Syntax and Variables (unlocked!)│
│ • Review: Package Management           │
└─────────────────────────────────────────┘
```

**What happened behind the scenes**:
1. Performance Analyzer calculated your mastery score
2. Journey Architect unlocked the next topic
3. Recommendation Agent suggested next steps
4. Motivation Agent provided encouragement
5. All decisions logged to database

---

## Tracking Your Progress

### Navigate to Progress Page

Click **"Progress"** in the navigation bar or visit:
```
http://localhost:4464/progress
```

### Progress Dashboard Components

#### 1. Mastery Radar Chart

Visual representation of your topic mastery:
```
        Python Functions (78.5%)
              ╱   ╲
             ╱     ╲
 Control    ╱       ╲    Basic Syntax
Structures ╱         ╲      (85%)
  (65%)   ╱           ╲
         ╱             ╲
        ╱               ╲
       ╱                 ╲
      ╱___________________╲
  OOP Basics            Data Types
    (45%)                 (92%)
```

**Interpretation**:
- **80-100%**: Advanced mastery (blue zone)
- **50-79%**: Intermediate mastery (green zone)
- **0-49%**: Beginner level (yellow zone)

#### 2. Quiz History Timeline

Chronological list of all quizzes taken:
```
📊 Quiz History

Oct 19, 2025 - Python Installation and Setup
Score: 4/5 (80%) | Difficulty: Medium | Time: 3m 45s

Oct 19, 2025 - Basic Syntax and Variables
Score: 5/5 (100%) | Difficulty: Easy | Time: 4m 12s

Oct 18, 2025 - Control Structures
Score: 3/5 (60%) | Difficulty: Medium | Time: 5m 30s
```

#### 3. Learning Insights

AI-generated summary from Performance Analyzer:
```
📈 Your Learning Insights

Overall Skill Level: Intermediate
Learning Velocity: High (improving quickly)

✨ Strengths:
• Basic Syntax (92% mastery)
• Data Types (90% mastery)

🎯 Knowledge Gaps:
• OOP Basics (45% mastery) - Recommended review
• Control Structures (65% mastery) - Continue practice

📊 Recent Trends:
• 15% improvement over last 7 days
• 5 quizzes completed this week
• Average score: 78%

💡 Recommendations:
• Focus on OOP concepts with easier difficulty
• Continue practicing Control Structures
• Ready to start Functions and Scope
```

#### 4. Journey Progress Bar

Visual completion tracker:
```
🗺️ Journey Progress

[██████████░░░░░░░░░░] 50% Complete

✅ Completed: 5/10 topics
🔄 In Progress: 2 topics
🔒 Locked: 3 topics
⭐ Milestones Reached: 1/2
```

---

## Next Steps

### Continue Learning

1. **Follow Your Journey**: Work through topics in order
2. **Take Quizzes**: Test your knowledge regularly
3. **Review Recommendations**: Explore suggested topics
4. **Track Progress**: Monitor your mastery scores
5. **Adjust Pace**: Update preferences as needed

### Explore Advanced Features

- **Restart Onboarding**: Click "⚙️ Restart Onboarding" to create a new profile
- **Agent Activity Log**: View `/adaptive/agent-decisions` to see AI reasoning
- **API Documentation**: Explore http://localhost:4465/docs
- **Export Progress**: (Coming soon) Download your learning data

### Troubleshooting

If you encounter issues:

1. **Check logs**: `docker compose logs backend`
2. **Restart services**: `docker compose restart`
3. **Clear cache**: Browser DevTools → Application → Clear cookies
4. **Reinitialize**: `docker compose exec backend python init_db.py`
5. **Full reset**: `docker compose down -v && docker compose up -d`

### Get Help

- **Documentation**: See `/docs` folder for detailed guides
- **API Reference**: `docs/API_REFERENCE.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **GitHub Issues**: Report bugs or request features

---

## Summary

You've learned how to:
- ✅ Install and configure AlkenaCode
- ✅ Complete onboarding with AI agents
- ✅ Navigate your personalized dashboard
- ✅ Start your learning journey
- ✅ Take adaptive quizzes
- ✅ Track your progress

**Your learning journey with 8 AI agents has begun!** 🚀

---

**Next Guide**: [Agent Development Guide](AGENT_DEVELOPMENT.md) - Learn how the AI agents work under the hood.
