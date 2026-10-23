```python
import unittest

from app import create_app
from extensions import db


class AppSmokeTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app()

        # Configure testing before initializing database tables.
        self.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SECRET_KEY="test-secret",
        )

        self.client = self.app.test_client()

        with self.app.app_context():
            # Create the test database tables.
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_page(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CivicShield", response.data)


if __name__ == "__main__":
    unittest.main()
```
