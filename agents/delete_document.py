import sqlite3

DB_PATH = "./batch_data.db"  # Update this if your database path is different
DOC_NAME_TO_DELETE = "GP 218-errors.pdf"

def delete_document_dynamic(db_path, doc_name):
    """
    Delete all instances of a document from the database dynamically by checking all tables.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Step 1: Get the doc_id for the document
        cursor.execute("SELECT doc_id FROM doc_info WHERE doc_name = ?;", (doc_name,))
        result = cursor.fetchone()
        if not result:
            print(f"Document '{doc_name}' not found in doc_info table.")
            conn.close()
            return
        doc_id = result[0]
        print(f"Found doc_id {doc_id} for document '{doc_name}'.")

        # Step 2: Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Step 3: Loop through tables and check if `doc_id` exists
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "doc_id" in columns:
                # Delete rows with matching doc_id
                cursor.execute(f"DELETE FROM {table} WHERE doc_id = ?;", (doc_id,))
                print(f"Deleted {cursor.rowcount} rows from {table} where doc_id = {doc_id}.")

        # Step 4: Delete the document from the doc_info table
        cursor.execute("DELETE FROM doc_info WHERE doc_id = ?;", (doc_id,))
        print(f"Deleted {cursor.rowcount} rows from doc_info table.")

        # Commit the changes
        conn.commit()
        print("All instances of the document deleted successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    delete_document_dynamic(DB_PATH, DOC_NAME_TO_DELETE)