import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import streamlit as st
import os
from datetime import datetime, timedelta
import hashlib
import logging
import io
import uuid
import base64

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Set page config
st.set_page_config(page_title="NeuroFlake", layout="wide", initial_sidebar_state="collapsed")

# Constants
CSV_FILE = 'user_interactions.csv'
MAX_RETRIES = 3
MAX_ROWS_DISPLAY = 1000
SIZE_LIMIT_MB = 190
DOWNLOAD_FOLDER = "downloads"
DOWNLOAD_EXPIRY_HOURS = 1  # Files will be deleted after this many hours

# Initialize CSV file
def init_csv():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=['timestamp', 'question', 'result', 'upvote', 'downvote', 'session_id']).to_csv(CSV_FILE, index=False)

# Load CSV file
@st.cache_data
def load_data():
    for _ in range(MAX_RETRIES):
        try:
            return pd.read_csv(CSV_FILE)
        except pd.errors.EmptyDataError:
            init_csv()
        except Exception as e:
            logging.error(f"Error loading CSV: {str(e)}")
    return pd.DataFrame()

# Append data to CSV
def append_to_csv(new_data):
    for _ in range(MAX_RETRIES):
        try:
            with open(CSV_FILE, 'a', newline='') as f:
                new_data.to_csv(f, header=f.tell()==0, index=False)
            return True
        except Exception as e:
            logging.error(f"Error appending to CSV: {str(e)}")
    return False

# Generate a session ID
def generate_session_id():
    return hashlib.md5(str(datetime.now()).encode()).hexdigest()

# Initialize app
def init_app():
    init_csv()
    if 'chat' not in st.session_state:
        st.session_state['chat'] = {"user_input": None, "bot_response_1": None, "bot_response_2": None}
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = generate_session_id()
    if 'last_question' not in st.session_state:
        st.session_state['last_question'] = None
    if 'last_sql' not in st.session_state:
        st.session_state['last_sql'] = None

# Mock function for SQL generation (replace with actual implementation)
def generate_sql(question):
    return f"SELECT * FROM sample_table WHERE condition = '{question}';"

# Mock function for query execution (replace with actual implementation)
def execute_query(sql):
    n_rows = 10000000  # Increased for testing large datasets
    return pd.DataFrame({
        'id': range(n_rows),
        'value': np.random.rand(n_rows),
        'category': np.random.choice(['A', 'B', 'C', 'D'], n_rows)
    })

# Handle user interaction
def handle_interaction(question, result):
    new_data = pd.DataFrame({
        'timestamp': [datetime.now()],
        'question': [question.strip().replace('\n', ' ')],
        'result': [result.strip().replace('\n', ' ')],
        'upvote': [0],
        'downvote': [0],
        'session_id': [st.session_state['session_id']]
    })
    append_to_csv(new_data)
    st.session_state['last_question'] = question.strip().replace('\n', ' ')

# Update feedback
def update_feedback(feedback_type, question):
    for _ in range(MAX_RETRIES):
        try:
            data = pd.read_csv(CSV_FILE)
            if not data.empty:
                matching_rows = data[data['question'] == question]
                if not matching_rows.empty:
                    latest_index = matching_rows.index[-1]
                    data.loc[latest_index, feedback_type] = 1
                    data.to_csv(CSV_FILE, index=False)
                    logging.info(f"Updated {feedback_type} for question: {question}")
                    return True
                else:
                    logging.warning(f"No matching question found for feedback: {question}")
            else:
                logging.warning("CSV file is empty")
            return False
        except Exception as e:
            logging.error(f"Error updating feedback: {str(e)}")
    return False

# Function to clean up old download files
def cleanup_old_files():
    now = datetime.now()
    for filename in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        if now - file_modified > timedelta(hours=DOWNLOAD_EXPIRY_HOURS):
            os.remove(file_path)

# Function to generate CSV file and return its content as a string
def generate_csv_file():
    if st.session_state['last_sql']:
        result_df = execute_query(st.session_state['last_sql'])
        csv = result_df.to_csv(index=False)
        return csv
    return None

# Function to create a download link
def get_download_link(csv_string, filename="full_result.csv"):
    b64 = base64.b64encode(csv_string.encode()).decode()
    href = f'data:file/csv;base64,{b64}'
    return f'<a href="{href}" download="{filename}">Download full CSV</a>'

# Main app
def main():
    init_app()
    cleanup_old_files()  # Clean up old files at the start of each session

    st.markdown('## NeuroFlake: AI-Powered Text-to-SQL for Snowflake')

    left_column, right_column = st.columns(2, gap="large")

    with right_column.container():
        with st.chat_message(name="user", avatar="user"):
            user_input_placeholder = st.empty()
        with st.chat_message(name="assistant", avatar="assistant"):
            bot_response_1_placeholder = st.empty()
            bot_response_2_placeholder = st.empty()
            info_placeholder = st.empty()
            download_placeholder = st.empty()

        user_input = st.text_area("Enter your question about the data:")

        button_column = st.columns(3)
        button_info = st.empty()

        with button_column[2]:
            if st.button("🚀 Generate SQL", key="generate_sql", use_container_width=True):
                if user_input:
                    user_input_placeholder.markdown(user_input)
                    try:
                        sql_response = generate_sql(user_input)
                        st.session_state['last_sql'] = sql_response
                        bot_response_1_placeholder.code(sql_response, language="sql")
                        
                        result_df = execute_query(sql_response)
                        
                        df_size = result_df.memory_usage(deep=True).sum() / (1024 * 1024)  # Size in MB
                        
                        limited_result = result_df.head(MAX_ROWS_DISPLAY)
                        bot_response_2_placeholder.dataframe(limited_result)
                        info_placeholder.info(f"Showing first {MAX_ROWS_DISPLAY} rows of {len(result_df)} total rows. Total size: {df_size:.2f} MB")
                        
                        # Generate CSV file and provide download link
                        csv_string = generate_csv_file()
                        if csv_string:
                            download_link = get_download_link(csv_string)
                            download_placeholder.markdown(download_link, unsafe_allow_html=True)
                        
                        result_response = f"Query executed successfully. {len(result_df)} rows returned."
                        handle_interaction(user_input, result_response)
                    except Exception as e:
                        logging.error(f"Error processing query: {str(e)}")
                        info_placeholder.error(f"An error occurred while processing your query: {str(e)}")

        with button_column[1]:
            if st.button("👍 Upvote", key="upvote", use_container_width=True):
                if st.session_state.get('last_question'):
                    if update_feedback('upvote', st.session_state['last_question']):
                        button_info.success("Thanks for your feedback! NeuroFlake Memory updated")
                    else:
                        button_info.error("Failed to update feedback. Please try again.")
                else:
                    button_info.warning("No recent question to upvote.")

        with button_column[0]:
            if st.button("👎 Downvote", key="downvote", use_container_width=True):
                if st.session_state.get('last_question'):
                    if update_feedback('downvote', st.session_state['last_question']):
                        button_info.warning("We're sorry the result wasn't helpful. Your feedback will help us improve!")
                    else:
                        button_info.error("Failed to update feedback. Please try again.")
                else:
                    button_info.warning("No recent question to downvote.")

        st.markdown("##### Sample questions you can ask:")
        sample_questions = [
            "What is the total revenue for each product category?",
            "Who are the top 5 customers by sales volume?",
            "What's the average order value by month?",
            "Which regions have seen the highest growth in the last quarter?",
            "What's the distribution of customer segments across different product lines?"
        ]
        
        for i, question in enumerate(sample_questions):
            question_columns = st.columns([7,1])
            with question_columns[0]:
                st.markdown(f"<div class='mytext'>{question}</div>", unsafe_allow_html=True)
            with question_columns[1]:
                if st.button(f"Ask", use_container_width=True, key=f'question{i}'):
                    user_input_placeholder.markdown(question)
                    try:
                        sql_response = generate_sql(question)
                        st.session_state['last_sql'] = sql_response
                        bot_response_1_placeholder.code(sql_response, language="sql")
                        result_df = execute_query(sql_response)
                        
                        df_size = result_df.memory_usage(deep=True).sum() / (1024 * 1024)  # Size in MB
                        
                        limited_result = result_df.head(MAX_ROWS_DISPLAY)
                        bot_response_2_placeholder.dataframe(limited_result)
                        info_placeholder.info(f"Showing first {MAX_ROWS_DISPLAY} rows of {len(result_df)} total rows. Total size: {df_size:.2f} MB")
                        
                        # Generate CSV file and provide download link
                        csv_string = generate_csv_file()
                        if csv_string:
                            download_link = get_download_link(csv_string)
                            download_placeholder.markdown(download_link, unsafe_allow_html=True)
                        
                        result_response = f"Query executed successfully. {len(result_df)} rows returned."
                        handle_interaction(question, result_response)
                    except Exception as e:
                        logging.error(f"Error processing sample question: {str(e)}")
                        info_placeholder.error(f"An error occurred while processing your query: {str(e)}")

    with left_column:
        st.markdown("""
        Welcome to NeuroFlake! 🧠❄️
        
        NeuroFlake is an AI-powered text-to-SQL tool designed to help you interact with your Snowflake data warehouse using natural language. Here's how it works:

        1. **Ask a Question**: Type your question about your data in plain English.
        2. **Generate SQL**: NeuroFlake will interpret your question and generate the appropriate SQL query.
        3. **View Results**: The query will be executed on your Snowflake database, and the results will be displayed.
        4. **Iterate**: Refine your question or ask follow-up questions to dive deeper into your data.

        You can use the sample questions provided or create your own. NeuroFlake is here to make data analysis accessible to everyone, regardless of their SQL expertise.

        Let's explore your data together!
        """)
        
        st.markdown('##### Sample Data Schema:')
        data = {
            'Table': ['CUSTOMERS', 'ORDERS', 'PRODUCTS', 'SALES'],
            'Columns': [
                'customer_id, name, email, segment',
                'order_id, customer_id, order_date, total_amount',
                'product_id, name, category, price',
                'sale_id, product_id, quantity, revenue'
            ]
        }
        df = pd.DataFrame(data)
        
        st.dataframe(df, height=500, use_container_width=True)

if __name__ == "__main__":
    main()
