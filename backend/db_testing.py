from db_manager import DatabaseManager

db = DatabaseManager()

while True:
    query = input("Query: ")
    print(db.runCustomQuery(query))
