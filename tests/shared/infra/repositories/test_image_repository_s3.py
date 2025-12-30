import base64
import os
import sys

sys.path.append(os.getcwd())

import pytest

from src.shared.helpers.errors.usecase_errors import ErrorWithImage
from src.shared.infra.repositories.image_repository_s3 import ImageRepositoryS3


class FakeS3Client:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.calls = []

    def put_object(self, **kwargs):
        if self.should_fail:
            raise RuntimeError("boom")
        self.calls.append(kwargs)
        return {"ok": True}


def test_image_repository_s3_put_image(monkeypatch):
    os.environ["STAGE"] = "TEST"
    client = FakeS3Client()
    monkeypatch.setattr("boto3.client", lambda *args, **kwargs: client)

    repo = ImageRepositoryS3()
    payload = base64.b64encode(b"data").decode("ascii")
    repo.put_image(base_64_image=payload, image_path="path/file.jpg", content_type="image/jpeg")

    assert client.calls
    call = client.calls[0]
    assert call["Body"] == b"data"
    assert call["Key"] == "path/file.jpg"
    assert call["ContentType"] == "image/jpeg"


def test_image_repository_s3_put_image_error(monkeypatch):
    os.environ["STAGE"] = "TEST"
    client = FakeS3Client(should_fail=True)
    monkeypatch.setattr("boto3.client", lambda *args, **kwargs: client)

    repo = ImageRepositoryS3()
    payload = base64.b64encode(b"data").decode("ascii")

    with pytest.raises(ErrorWithImage):
        repo.put_image(base_64_image=payload, image_path="path/file.jpg", content_type="image/jpeg")
