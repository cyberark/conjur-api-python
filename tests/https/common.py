class MockResponse:
    def __init__(self, text: str, status: int):
        self._text = text
        self.status = status

    async def read(self):
        pass

    async def text(self, encoding: str = 'utf-8'):
        return self._text

    def raise_for_status(self):
        if self.status >= 400:
            raise Exception(f"Bad status: {self.status}")

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self
