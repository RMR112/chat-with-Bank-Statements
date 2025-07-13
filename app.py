import pdfplumber
import pandas as pd
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv
import os
import re

load_dotenv()

def extract_table_safely(pdf_path):
    import pdfplumber
    import pandas as pd

    all_rows = []
    header = None
    current_row = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            for row in table:
                # Clean each cell
                cleaned = [str(cell).replace('\n', ' ').strip() if cell else "" for cell in row]

                # Detect header: first row with at least 5 non-empty cells
                if not header and sum(1 for cell in cleaned if cell.strip()) >= 5:
                    header = cleaned
                    continue

                if not header:
                    continue

                # Fix rows that are shorter or longer than the header
                if len(cleaned) < len(header):
                    cleaned += [""] * (len(header) - len(cleaned))  # pad
                elif len(cleaned) > len(header):
                    cleaned = cleaned[:len(header)]  # trim

                all_rows.append(cleaned)

    if not header or not all_rows:
        print("❌ No valid table found in the PDF.")
        return pd.DataFrame()

    # Create DataFrame
    df = pd.DataFrame(all_rows, columns=header)

    # Normalize column names
    df.columns = [col.strip().replace('\n', ' ').replace('\r', '') for col in df.columns]

    print("\n🧪 Cleaned Columns in DataFrame:", df.columns.tolist())
    print(df.head())

    return df


def clean_description(text):
    if not isinstance(text, str):
        return ""
    
    # Remove newline characters and excess spaces
    cleaned = re.sub(r'\s+', ' ', text.strip())

    # Optional: Remove duplicate slashes like '///' to '/'
    cleaned = re.sub(r'/+', '/', cleaned)

    return cleaned



def clean_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        col_clean = col.lower().strip()

        if "date" in col_clean:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

        if "withdrawal" in col_clean or "deposit" in col_clean or "amount" in col_clean:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def save_to_sqlite(df: pd.DataFrame, db_path: str = "transactions.db", table_name: str = "transactions"):
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    return conn

def get_table_schema(conn, table_name: str = "transactions") -> str:
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return "\n".join([f"{col[1]} ({col[2]})" for col in cursor.fetchall()])

def generate_sql_from_query(nl_query: str, table_schema: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
You are a helpful assistant that converts natural language queries into SQL.

Schema of the table:
{table_schema}

Examples:
Q: What is the total withdrawal for June 2025?
A: SELECT SUM("Withdrawal Amount (INR )") FROM transactions WHERE strftime('%Y-%m', "Value Date") = '2025-06';

Q: List top 5 deposits in May 2025
A: SELECT * FROM transactions WHERE strftime('%Y-%m', "Value Date") = '2025-05' ORDER BY "Deposit Amount (INR )" DESC LIMIT 5;

Now answer:
Q: {nl_query}
A: 
Return only the SQL query. Do not include any explanation. Remove ```sql and ``` markers..
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content.strip()

def execute_sql(sql: str, conn):
    try:
        df_result = pd.read_sql_query(sql, conn)
        return df_result
    except Exception as e:
        return f"❌ Error running SQL:\n{e}\n\nQuery:\n{sql}"

def main():
    pdf_path = input("📄 Enter the path to your PDF file: ").strip()
    #pdf_path = "data/OpTransactionHistoryTpr08-07-2025.pdf"
    if not os.path.isfile(pdf_path):
        print("❌ File not found. Please check the path and try again.")
        exit(1)
    print(f"PDF file found: {pdf_path}")
    print("📥 Reading PDF & extracting data...")
    
    df = extract_table_safely(pdf_path)
    #df['Description'] = df['Description'].apply(clean_description)
    df = clean_dataframe_types(df)
    print(f"✅ Extracted {len(df)} rows.")

    conn = save_to_sqlite(df)
    schema = get_table_schema(conn)

    while True:
        nl_query = input("\n💬 Ask your query (or type 'exit'): ")
        if nl_query.lower() == "exit":
            break

        sql_query = generate_sql_from_query(nl_query, schema)
        print(f"\n🧠 Generated SQL:\n{sql_query}")
        result = execute_sql(sql_query, conn)
        print("\n📊 Result:")
        print(result)

if __name__ == "__main__":
    print("🧠 Starting bank statement processor...")
    main()
