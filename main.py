import streamlit as st
from pymongo import MongoClient
import os
import dotenv

dotenv.load_dotenv()

# Load environment variables
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Fetch all collection names from the database
def get_collections():
    try:
        collections = db.list_collection_names()
        return collections
    except Exception as e:
        st.error(f"Error fetching collections: {e}")
        return []

# Fetch data from MongoDB
def fetch_data(collection_name, page, page_size, search_query=None, sample_doc=None):
    try:
        collection = db[collection_name]
        query = {}
        if search_query:
            # Fetch a sample document to get the keys
            print(sample_doc, sample_doc)
            if sample_doc:
                keys = list(sample_doc.keys())
                # Create a regex query for each key
                regex_query = {"$regex": search_query, "$options": "i"}
                query = {"$or": [{key: regex_query} for key in keys]}
        data = list(collection.find(query).skip(page * page_size).limit(page_size))
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []

# Update data in MongoDB
def update_data(collection_name, id, obj):
    try:
        collection = db[collection_name]
        collection.update_one({"_id": id}, {"$set": obj})
        st.success("Data updated successfully!")
    except Exception as e:
        st.error(f"Error updating data: {e}")

# Authentication function
def authenticate():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid username or password")

# Main Streamlit app
def main():
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        authenticate()
        return

    if "sample_doc" not in st.session_state:
        st.session_state.sample_doc = {}

    st.title("Faceon Admin")

    # Fetch and display available collections
    collections = get_collections()
    if collections:
        selected_collection = st.selectbox("Select a collection", collections)
        collection = db[selected_collection]

        st.subheader(f"Collection: {selected_collection}")

        # Search filter
        search_query = st.text_input("Search", value="")

        # Pagination controls in a single row
        col1, col2 = st.columns([1, 1])
        with col1:
            page = st.number_input("Page", min_value=0, value=0)
        with col2:
            page_size = st.number_input("Page Size", min_value=1, value=10)

        # Fetch data with the current sample_doc
        data = fetch_data(selected_collection, page, page_size, search_query, st.session_state.sample_doc)

        if data:
            for idx, item in enumerate(data):
                id = item["_id"]
                obj = {}

                langs = list(set(item.get('translations', {}).keys()) | set(['en', 'zh-CN', 'zh-TW']))

                for k, v in item.items():
                    lower_k = k.lower()
                    if 'id' in lower_k or 'image' in lower_k or 'photo' in lower_k: continue
                    if isinstance(v, str):
                        text = st.text_input(f"Edit {k}", value=v, key=f"input_{id}_{k}")
                        obj[k] = text
                        for lang in langs:
                            t_v = "" 
                            if item.get('translations', {}).get(lang, {}).get(k, None):
                                t_v = item['translations'][lang][k]

                            new_text = st.text_input(f"Edit {k} {lang}", value=t_v, key=f"input_{id}_{lang}_{k}")
                            
                            obj[f'translations.{lang}.{k}'] = new_text
                
                # Update sample_doc for the next fetch
                st.session_state.sample_doc = obj

                # Update button
                if st.button(f"Update (ID {id})", key=f"update_{id}"):
                    update_data(selected_collection, id, {k : v for k, v in obj.items() if v})
                st.write(f"---------")
        else:
            st.warning("No data found in the selected collection.")
    else:
        st.warning("No collections found in the database.")

if __name__ == "__main__":
    main()