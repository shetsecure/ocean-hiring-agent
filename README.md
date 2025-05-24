# Team Compatibility Analyzer

A comprehensive Python tool that analyzes compatibility between job candidates and existing software engineering teams using the Big Five personality traits and advanced AI analysis.

## 🌟 Features

- **Multi-format Support**: Works with direct personality traits or extracts them from interview responses
- **AI-Powered Analysis**: Uses Mistral AI for sophisticated compatibility assessment
- **Mathematical Scoring**: Calculates quantitative compatibility scores
- **Comprehensive Reports**: Generates detailed analysis with recommendations
- **Robust Error Handling**: Includes fallback mechanisms and data validation
- **Professional Output**: Beautiful console output and detailed JSON reports

## 📁 Project Structure

The project is now organized into modular components for better maintainability:

```
├── main.py                     # Main entry point and execution script
├── compatibility_analyzer.py    # Core analyzer class
├── rate_limiter.py             # Rate limiting functionality
├── personality_extractor.py    # AI-powered trait extraction
├── utils.py                    # Utility functions and formatting
├── __init__.py                 # Package initialization
├── requirements.txt            # Python dependencies
├── env.example                 # Environment variables template
├── README.md                   # Documentation
├── data/                       # Data files directory
│   ├── team.json              # Team member data
│   ├── candidate_alice_smith.json   # Alice Smith's interview data
│   ├── candidate_bob_johnson.json   # Bob Johnson's interview data
│   ├── candidate_carol_davis.json   # Carol Davis's interview data
│   ├── candidate_david_lee.json     # David Lee's interview data
│   └── compatibility_scores.json    # Generated analysis results
└── [other files...]
```

### Module Overview

- **`main.py`**: Entry point script with execution logic and error handling
- **`CompatibilityAnalyzer`**: Core analysis engine with mathematical scoring and AI integration
- **`RateLimiter`**: Handles API rate limiting with exponential backoff and jitter
- **`PersonalityTraitsExtractor`**: Extracts Big Five traits from interview responses using AI
- **`Utils`**: Formatting functions for console output and result presentation

## 📋 Requirements

- Python 3.9 or higher
- Mistral AI API key
- Required dependencies (see `requirements.txt`)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project files
cd your-project-directory

# Install dependencies
pip install -r requirements.txt
```

### 2. Set up your API key

**Option A: Environment Variable**
```bash
export MISTRAL_API_KEY="your_mistral_api_key_here"
# Optional: Set rate limit (default: 1 request per second)
export MISTRAL_REQUESTS_PER_SECOND=1.0
# Optional: Set model (default: mistral-small-latest)
export MISTRAL_MODEL=mistral-small-latest
```

**Option B: Create .env file**
```bash
# Copy the example file
cp env.example .env

# Edit .env and add your API key and configuration
# MISTRAL_API_KEY=your_mistral_api_key_here
# MISTRAL_REQUESTS_PER_SECOND=1.0
# MISTRAL_MODEL=mistral-small-latest
```

### 3. Configure Rate Limiting (Important!)

The script includes built-in rate limiting to respect your Mistral AI plan limits:

- **Free Tier**: 1 request per second (default setting)
- **Paid Tiers**: Higher limits available - adjust `MISTRAL_REQUESTS_PER_SECOND` accordingly

⚠️ **Rate Limiting Notice**: 
- The script will automatically pace API requests to respect your limits
- For multiple candidates needing AI trait extraction, this may extend analysis time
- Progress indicators will show estimated completion time
- Rate limit violations trigger automatic retry with exponential backoff

### 4. Configure Mistral AI Model (Optional)

The script supports different Mistral AI models for varying levels of analysis quality and cost:

- **`mistral-small-latest`** (default): Fastest and most cost-effective option
- **`mistral-medium-latest`**: Better analysis quality, higher cost
- **`mistral-large-latest`**: Best analysis quality, highest cost

Set the model using the `MISTRAL_MODEL` environment variable:
```bash
export MISTRAL_MODEL=mistral-medium-latest
```

⚠️ **Model Selection Tips**:
- Use `mistral-small-latest` for basic compatibility analysis and cost optimization
- Use `mistral-medium-latest` for more nuanced insights and better trait extraction
- Use `mistral-large-latest` for the most sophisticated analysis and complex scenarios
- Check [Mistral AI pricing](https://mistral.ai/technology/#pricing) for cost implications

### 5. Prepare your data files

The script expects team data and individual candidate files in the `data/` directory:

#### `data/team.json` - Team member data
```json
{
  "team": [
    {
      "id": "T1",
      "name": "Emma Dupont",
      "position": "Senior Backend Engineer",
      "big_five": {
        "openness": 0.85,
        "conscientiousness": 0.92,
        "extraversion": 0.65,
        "agreeableness": 0.78,
        "neuroticism": 0.30
      }
    }
  ]
}
```

#### `data/candidate_*.json` - Individual candidate files
Each candidate should have their own JSON file named `candidate_[name].json`:

**Example: `data/candidate_alice_smith.json`**
```json
{
  "candidate": {
    "id": "SE1",
    "name": "Alice Smith",
    "position": "Software Engineer",
    "responses": [
      {
        "question": "How do you handle technical disagreements?",
        "answer": "I focus on data-driven discussions and always remain open to alternative approaches.",
        "trait": "Openness"
      }
    ]
  }
}
```

**Note**: The script automatically detects all `candidate_*.json` files in the `data/` directory and processes them individually.

### Adding New Candidates

To add a new candidate, simply create a new JSON file in the `data/` directory following the naming pattern `candidate_[name].json`. For example:

- `data/candidate_jane_doe.json`
- `data/candidate_michael_smith.json`

The script will automatically detect and process any new candidate files on the next run.

### 6. Run the analysis

```bash
python main.py
```

## 📊 Data Format Support

### Team Data Formats

The script supports multiple team data formats:

**Format 1: Using `big_five`**
```json
{
  "team": [
    {
      "id": "T1",
      "name": "John Doe",
      "position": "Developer",
      "big_five": {
        "openness": 0.75,
        "conscientiousness": 0.85,
        "extraversion": 0.60,
        "agreeableness": 0.80,
        "neuroticism": 0.30
      }
    }
  ]
}
```

**Format 2: Using `personality_traits`**
```json
{
  "team_members": [
    {
      "id": "TM001", 
      "name": "Jane Smith",
      "role": "Senior Engineer",
      "personality_traits": {
        "openness": 0.80,
        "conscientiousness": 0.90,
        "extraversion": 0.70,
        "agreeableness": 0.75,
        "neuroticism": 0.25
      }
    }
  ]
}
```

### Candidate Data Formats

**Individual Candidate Files**: Each candidate has their own JSON file in the `data/` directory following the pattern `candidate_*.json`.

**Format 1: Direct personality traits**
```json
{
  "candidate": {
    "id": "C1",
    "name": "Alice Johnson",
    "position": "Software Engineer",
    "big_five": {
      "openness": 0.75,
      "conscientiousness": 0.80,
      "extraversion": 0.65,
      "agreeableness": 0.70,
      "neuroticism": 0.35
    }
  }
}
```

**Format 2: Interview responses (AI extraction)**
```json
{
  "candidate": {
    "id": "SE1",
    "name": "Bob Wilson",
    "position": "Software Engineer",
    "responses": [
      {
        "question": "Describe your ideal work environment.",
        "answer": "I thrive in collaborative environments where team members actively share knowledge.",
        "trait": "Extraversion"
      }
    ]
  }
}
```

**Note**: The script automatically detects all `candidate_*.json` files in the `data/` directory and processes them individually.

### Adding New Candidates

To add a new candidate, simply create a new JSON file in the `data/` directory following the naming pattern `candidate_[name].json`. For example:

- `data/candidate_jane_doe.json`
- `data/candidate_michael_smith.json`

The script will automatically detect and process any new candidate files on the next run.

## 🎯 Output

### Console Output
The script provides a beautiful, formatted console output with:
- 📊 Analysis metadata and overview
- 📈 Candidate pool summary
- 🧑‍💼 Individual candidate analysis
- 🎯 Recommendations and scores

### JSON Report (`data/compatibility_scores.json`)
Detailed JSON report including:
- **Analysis Metadata**: Timestamps, file info, version
- **Team Summary**: Team member profiles
- **Mathematical Analysis**: Quantitative compatibility scores
- **AI Analysis**: Comprehensive personality and team dynamics assessment
- **Recommendations**: Actionable hiring recommendations
- **Team Insights**: Pool-level analysis and top candidates

## 🧠 Analysis Components

### 1. Mathematical Compatibility
- **Trait Similarity**: Calculates similarity between personality traits
- **Team Harmony**: Measures how well the candidate fits with all team members
- **Individual Scores**: Compatibility with each team member
- **Variance Analysis**: Assesses consistency across the team

### 2. AI-Powered Analysis
- **Personality Fit**: Deep analysis of trait complementarity
- **Team Dynamics**: Impact on team culture and collaboration
- **Growth Opportunities**: Development and mentoring potential
- **Risk Assessment**: Potential challenges and mitigation strategies

### 3. Combined Recommendations
- **Overall Score**: Mathematical + AI assessment
- **Confidence Level**: AI confidence in the analysis
- **Status Categories**: 
  - `HIGHLY RECOMMENDED` (0.8+ score, high confidence)
  - `RECOMMENDED` (0.7+ score, good confidence)
  - `CONDITIONAL` (0.6+ score, needs additional evaluation)
  - `