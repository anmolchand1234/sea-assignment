from backend.app.db.session import engine, Base
import backend.app.models

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created successfully.")

