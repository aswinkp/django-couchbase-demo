from django.test import TestCase
from couch.models import *
# Create your tests here.

class TestCase(TestCase):
    def savetest(self):
        article = Article(title = "New Article")
        article2 = Article(title = "Second Article")
        blog = Blog(url = "4sw.in", articles = [article, article2])
        articles = [Article(title = "Third Article"),Article(title = "Fourth Article")]
        blog2 = Blog(url = "bogger.com", articles = articles)
        pub = Publisher(name = "Famous Publications")
        pub2 = Publisher(name = "Much more Famous Publications")
        book = Book(name = "First Book", pages = 250, publisher = pub)
        book2 = Book(name = "Second Book", pages = 340, publisher = pub2)
        address = Address(street = "Anna Nagar", city = "Chennai")
        author = Author(name = "Aswin", blog = blog, books = [book, book2], address=address)
        author.save()

    def mrftest(self):
        authors = [CBAuthorRef(name="Aswin", age="50"), CBAuthorRef(name="Aswin2", age="502")]
        article = CBArticle(title="BBBBBBBB", year_published=2010, is_draft=True, authors=authors)
        article.save()
