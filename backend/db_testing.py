from db_manager import DatabaseManager

db = DatabaseManager()

while True:
    query = input("Query: ")
    print(db.runCustomQuery(query))
    print(db.getEventDetails(event_id = 19))
