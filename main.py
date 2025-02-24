import os
import dotenv
import streamlit as st
from pymongo import MongoClient

# Load environment variables from .env file
dotenv.load_dotenv()
MONGO_URI_DEV = os.getenv("MONGO_URI_DEV")
MONGO_URI_RELEASE = os.getenv("MONGO_URI_RELEASE")
DB_NAME = os.getenv("DB_NAME")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# dev connection
client_dev = MongoClient(MONGO_URI_DEV)
db_dev = client_dev[DB_NAME]

#release connection
client_rel = MongoClient(MONGO_URI_RELEASE)
db_rel = client_rel[DB_NAME]


def get_collections():
    
    try:
        collections = db_dev.list_collection_names()
        return collections
    except Exception as e:
        st.error(f"Error fetching collections: {e}")
        return []


def fetch_data(collection_name, page, page_size, search_query=None, sample_doc=None):
    
    try:
        collection = db_dev[collection_name]
        query = {}
        if search_query and sample_doc:
            keys = list(sample_doc.keys())
            regex_query = {"$regex": search_query, "$options": "i"}
            query = {"$or": [{key: regex_query} for key in keys]}
        data = list(
            collection.find(query)
            .skip(page * page_size)
            .limit(page_size)
        )
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return []


def update_data(collection_name, doc_id, update_obj):
    try:
        collection = db_dev[collection_name]
        collection.update_one({"_id": doc_id}, {"$set": update_obj})
        st.success("Data updated successfully!")
    except Exception as e:
        st.error(f"Error updating data: {e}")


def update_release_db(collection_name):
    
    try:
        
        for obj in db_dev[collection_name].find({}): 
            db_rel[collection_name].find_one_and_update(obj['_id'], {"$set": obj})
        
        st.success("Release database updated successfully!")
    except Exception as e:
        st.error(f"Error updating release database: {e}")




def authenticate():
    
    st.title("Faceon Admin Dashboard", anchor=False)
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if username_input == USERNAME and password_input == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid username or password")


def main():
    """
    Main function to run the Streamlit admin interface with an updated professional layout.
    """
    st.set_page_config(layout="wide", page_title="Faceon Admin", page_icon="🏥")
    
    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "sample_doc" not in st.session_state:
        st.session_state.sample_doc = {}

    # If the user is not authenticated, show the login screen.
    if not st.session_state.logged_in:
        authenticate()
        return

    st.title("Faceon Admin Dashboard", anchor=False)

    # Get available collections from the database.
    collections = get_collections()
    if not collections:
        st.warning("No collections found in the database.")
        return

    # Top controls: Collection selector, Search bar, and Pagination in a single row.
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        with col1:
            selected_collection = st.selectbox("Select Collection", collections)
        with col2:
            search_query = st.text_input("Search", value="")
        with col3:
            page = st.number_input("Page", min_value=0, value=0, step=1)
        with col4:
            page_size = st.number_input("Page Size", min_value=1, value=10, step=1)


    with st.container():
        if st.button("Update Release DB", key="update_release", use_container_width=True):
            update_release_db(selected_collection)
            
    st.markdown("---")
    st.subheader(f"Collection: {selected_collection}")

    # Fetch data from the selected collection.
    data = fetch_data(selected_collection, page, page_size, search_query, st.session_state.sample_doc)

    if data:
        for item in data:
            doc_id = item["_id"]
            update_fields = {}

            # Determine available languages (default plus any from the document)
            default_langs = {"en", "zh-CN", "zh-TW"}
            available_langs = set(item.get("translations", {}).keys()) | default_langs
            langs = list(available_langs)

            # Use an expander and form for a cleaner update UI per document
            with st.expander(f"Document ID: {doc_id}", expanded=True):
                with st.form(key=f"form_{doc_id}"):
                    for key, value in item.items():
                        if any(sub in key.lower() for sub in ["id", "image", "photo"]):
                            continue
                        if isinstance(value, str):
                            new_value = st.text_input(
                                f"Edit {key}",
                                value=value,
                                key=f"input_{doc_id}_{key}"
                            )
                            update_fields[key] = new_value

                            # Provide translation inputs for each language.
                            for lang in langs:
                                translated_value = ""
                                if item.get("translations", {}).get(lang, {}).get(key):
                                    translated_value = item["translations"][lang][key]
                                new_translated = st.text_input(
                                    f"Edit {key} [{lang}]",
                                    value=translated_value,
                                    key=f"input_{doc_id}_{lang}_{key}"
                                )
                                update_fields[f"translations.{lang}.{key}"] = new_translated

                    submitted = st.form_submit_button("Update")
                    if submitted:
                        # Update only if the field has a non-empty value.
                        filtered_update = {k: v for k, v in update_fields.items() if v}
                        update_data(selected_collection, doc_id, filtered_update)
                        st.experimental_rerun()
                
    else:
        st.warning("No data found in the selected collection.")


if __name__ == "__main__":
    main()
