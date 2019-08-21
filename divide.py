import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



def main():

    f = open("books.csv")
    reader = csv.reader(f)
        
    isbn_list = ()
    title_list = ()
    author_list = ()
    year_list = ()


if __name__ == "__main__":
    main()
