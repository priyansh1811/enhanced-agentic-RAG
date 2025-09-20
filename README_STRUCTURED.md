# Archon: The Proactive & Adaptive Analyst

A fourth-generation AI agent that goes beyond reactive reasoning to become a proactive and adaptive analytical partner with advanced capabilities including long-term memory, proactive monitoring, and multi-modal vision analysis.

## 🚀 Features

- **The Scribe (Long-Term Memory)**: Persistent cognitive memory store for learning from past interactions
- **The Watchtower (Proactive Monitoring)**: Monitors for significant events and proactively alerts users
- **The Oracle (Multi-Modal Vision)**: Interprets charts and graphs in financial documents
- **Advanced Reasoning Engine**: Multi-step workflow with gatekeeper, planner, executor, auditor, and synthesizer
- **Specialist Agents**: Dedicated tools for document retrieval, SQL analysis, trend analysis, and live data
- **Comprehensive Evaluation**: LLM-as-a-judge evaluation and red team testing
- **Robust Architecture**: Built with LangChain, LangGraph, and Qdrant for production use

## 📁 Project Structure

```
enhanced Agentic RAG/
├── src/                          # Main source code
│   ├── agents/                   # Agent modules
│   │   ├── tools.py             # Specialist tools
│   │   ├── reasoning_engine.py  # Advanced reasoning workflow
│   │   └── specialist_agents.py # Agent orchestration
│   ├── data/                    # Data processing
│   │   ├── acquisition.py       # SEC filing download
│   │   ├── processor.py         # Document processing & enrichment
│   │   └── storage.py           # Vector & memory stores
│   ├── evaluation/              # Testing & evaluation
│   │   ├── evaluator.py         # Performance evaluation
│   │   └── red_team.py          # Adversarial testing
│   ├── config/                  # Configuration
│   │   └── settings.py          # Environment settings
│   ├── utils/                   # Utilities
│   │   ├── logging.py           # Logging setup
│   │   └── helpers.py           # Helper functions
│   └── main.py                  # Main entry point
├── examples/                    # Usage examples
│   ├── basic_usage.py           # Basic usage example
│   └── evaluation_example.py    # Evaluation example
├── data/                        # Data storage
│   ├── raw/                     # Raw data files
│   ├── processed/               # Processed data
│   └── vector_store/            # Vector database
├── logs/                        # Log files
├── tests/                       # Test files
├── docs/                        # Documentation
├── requirements.txt             # Python dependencies
├── config.env.example          # Environment variables template
└── README_STRUCTURED.md        # This file
```

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd enhanced\ Agentic\ RAG
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp config.env.example .env
   # Edit .env with your API keys
   ```

4. **Required API Keys**:
   - OpenAI API key (required)
   - Google API key (optional)
   - Tavily API key (optional)
   - LangSmith API key (optional)
   - Qdrant API key (optional)

## 🚀 Quick Start

### Basic Usage

```python
from src.main import Archon

# Initialize Archon
archon = Archon()

# Set up the system
archon.setup()

# Ask a question
result = archon.analyze("What is Microsoft's revenue trend over the last 2 years?")
print(result['response'])
```

### Command Line Interface

```bash
# Set up the system
python -m src.main --setup

# Ask a question
python -m src.main --question "What are Microsoft's main business risks?"

# Run evaluation
python -m src.main --evaluate

# Run red team testing
python -m src.main --red-team

# Start interactive mode
python -m src.main --interactive
```

## 📊 Architecture

### Data Processing Pipeline

1. **Data Acquisition**: Downloads SEC filings using `sec-edgar-downloader`
2. **Document Processing**: Parses HTML using `unstructured` library
3. **Chunking**: Structure-aware chunking preserving tables and formatting
4. **Enrichment**: LLM-powered metadata generation for each chunk
5. **Vector Storage**: Embedding generation and storage in Qdrant
6. **Memory Storage**: Persistent memory for learning and context

### Reasoning Engine

The reasoning engine follows a sophisticated multi-step workflow:

1. **Gatekeeper**: Validates questions and detects ambiguity
2. **Planner**: Creates step-by-step execution plans
3. **Tool Executor**: Executes specialist tools based on the plan
4. **Auditor**: Verifies output quality and consistency
5. **Router**: Decides next steps based on verification results
6. **Synthesizer**: Combines results into comprehensive responses

### Specialist Tools

- **Librarian Tool**: Multi-step RAG for document retrieval
- **Analyst SQL Tool**: Structured data querying
- **Analyst Trend Tool**: Time-series analysis and trend detection
- **Scout Tool**: Live web data and news retrieval

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here

# Database Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key_here

# Application Configuration
COMPANY_TICKER=MSFT
COMPANY_NAME=Microsoft
COMPANY_EMAIL=analyst@archon.ai

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/archon.log

# Memory and Storage
MEMORY_STORE_PATH=data/memory_store.json
VECTOR_STORE_PATH=data/vector_store
```

### Model Configuration

You can customize the models used in `src/config/settings.py`:

```python
# Model Configuration
embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2")
llm_model: str = Field("gpt-4")
temperature: float = Field(0.1)
max_tokens: int = Field(4000)
```

## 📈 Evaluation

### Performance Evaluation

The system includes comprehensive evaluation capabilities:

- **Relevance Scoring**: How well responses address the question
- **Accuracy Scoring**: Factual correctness of information
- **Completeness Scoring**: Thoroughness of responses
- **Speed Metrics**: Response time and token usage
- **Quality Rates**: High-quality vs low-quality response rates

### Red Team Testing

Adversarial testing to ensure robustness:

- **Bias Testing**: Checks for biased or unfair responses
- **Fact-Checking**: Tests accuracy and fact verification
- **Ambiguity Handling**: Tests response to unclear questions
- **Edge Case Testing**: Boundary condition testing
- **Ethical Boundaries**: Tests adherence to ethical guidelines

## 🧪 Examples

### Basic Analysis

```python
from src.main import Archon

archon = Archon()
archon.setup()

# Financial analysis
result = archon.analyze("Analyze Microsoft's cloud revenue growth")
print(result['response'])

# Risk assessment
result = archon.analyze("What are the main risks in Microsoft's annual report?")
print(result['response'])
```

### Evaluation

```python
# Run comprehensive evaluation
test_questions = [
    "What is Microsoft's revenue trend?",
    "What are the main business risks?",
    "How has cloud growth performed?"
]

results = archon.evaluate(test_questions)
print(f"Overall Score: {results['evaluation_metrics']['avg_overall']}/5")
```

### Red Team Testing

```python
# Test robustness
red_team_results = archon.red_team_test(num_questions=10)
print(f"Robustness Rate: {red_team_results['robustness_rate']}")
```

## 🔍 Advanced Features

### Long-Term Memory

The system maintains persistent memory across conversations:

```python
# Add insights to memory
archon.memory_store.add_insight("Microsoft's cloud growth is accelerating", "financial")

# Retrieve insights
insights = archon.memory_store.get_insights("financial")
```

### Proactive Monitoring

Set up monitoring for important events:

```python
# This would be implemented in a production system
# for monitoring new SEC filings, news, etc.
```

### Multi-Modal Analysis

Analyze charts and graphs in documents:

```python
# This would be implemented for vision analysis
# of charts and graphs in financial documents
```

## 🚀 Deployment

### Local Development

1. Set up Python environment
2. Install dependencies
3. Configure environment variables
4. Run setup: `python -m src.main --setup`
5. Start using: `python -m src.main --interactive`

### Production Deployment

1. Use a production-grade vector database (Qdrant Cloud)
2. Set up proper logging and monitoring
3. Configure API rate limiting
4. Implement proper error handling
5. Set up automated backups for memory store

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) and [LangGraph](https://langchain.com/langgraph)
- Vector storage powered by [Qdrant](https://qdrant.tech/)
- Document processing with [Unstructured](https://unstructured.io/)
- Inspired by [Uber's Enhanced Agentic RAG](https://www.uber.com/en-PK/blog/enhanced-agentic-rag/)

## 📞 Support

For questions and support, please open an issue in the repository or contact the development team.

---

**Archon v4.0** - The Proactive & Adaptive Analyst
