from src.utils.database import db, get_collection

# List collections
print("Collections:", db.list_collection_names())

# Insert a test document
test_col = get_collection("test_collection")
result = test_col.insert_one({"name": "Test", "value": 123})
print("Inserted ID:", result.inserted_id)

# Retrieve it
doc = test_col.find_one({"_id": result.inserted_id})
print("Retrieved document:", doc)

# Clean up
test_col.delete_one({"_id": result.inserted_id})
print("Test completed ✅")
