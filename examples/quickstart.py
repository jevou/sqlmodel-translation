from fastapi import FastAPI, Header
from sqlmodel import Field, Session, SQLModel, StaticPool, create_engine, select

from modeltranslation import TranslationOptions, Translator, apply_translation

engine = create_engine(
    "sqlite:///db.sqlite",
    echo=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def create_db_and_tables() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


class BookBase(SQLModel):
    title: str
    author: str
class Book(BookBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


translator = Translator(
    default_language="en",
    languages=("en", "pl"),
    #fallback_languages={"default": ("pl",)},
)


@translator.register(Book)
class BookTranslationOptions(TranslationOptions):
    fields = ("title",)


create_db_and_tables()

books = [
    Book(title_en="english_title_1", title_pl="polish_title_1", author="J.R.R. Tolkien"),
    Book(title_en="english_title_2", title_pl="polish_title_2", author="Harper Lee"),
]

with Session(engine) as session:
    session.add_all(books)
    session.commit()


app = FastAPI()

apply_translation(app, translator)


@app.get("/all")
def get_books(
        accept_language: str = Header(None),
    ) -> list[Book]:
    with Session(engine) as session:
        return session.exec(select(Book)).all()


@app.get("/titles")
def get_titles(
        accept_language: str = Header(None),
    ) -> list[str]:
    with Session(engine) as session:
        return session.exec(select(Book.title)).all()


@app.post("/create")
def create_book(
        book: Book,
        accept_language: str = Header(None),
    ) -> Book:
    with Session(engine) as session:
        db_book = Book.model_validate(book)
        print(db_book)
        session.add(book)
        session.commit()
        session.refresh(book)
        return book
