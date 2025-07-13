# Chat with Bank Statements (PDF → SQL)

A Python-based tool to extract, clean, and query bank statement PDFs using natural language. It uses `pdfplumber` to parse bank statements, stores them in SQLite, and queries using OpenAI's LLM.

---

## 🚀 Features

- Extracts transaction tables from bank statement PDFs
- Cleans messy columns like `Description`, `Debit`, `Branch Code`
- Converts natural language to SQL using OpenAI API (GPT-4o or GPT-3.5)
- Stores data in SQLite for robust querying
- Modular codebase to support multiple banks in future

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/rag-chat-bank-statements.git
cd chat-with-Bank-Statements
```

### 2. Setup Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate   # On Windows
```

### 3. Install Dependencies and Setup .env

```bash
pip install -r requirements.txt

Create a .env file in the project root:
OPENAI_API_KEY=your-api-key-here
```

## How It Works

- Prompts user for a PDF bank statement

- Extracts and cleans transaction data

- Stores it into a SQLite database

User can enter questions like:

"What is the total debit in June 2025?"

"Top 5 highest credit transactions in May?"

OpenAI translates the question to SQL and shows the result

### Example Query

💬 Ask your query (or type 'exit'): What is the total debit in May 2025?

🧠 Generated SQL:
SELECT SUM("Debit") FROM transactions WHERE strftime('%Y-%m', "Value Date") = '2025-05';

📊 Result:
SUM("Debit")

---

     6842.50
