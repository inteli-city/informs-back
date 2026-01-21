from src.shared.domain.repositories.image_repository_interface import IImageRepository


class ImageRepositoryMock(IImageRepository):

    def generate_presigned_url(self, image_path: str, mimetype: str, expires_in: int = 3600) -> str:
        return f"https://mock-presigned-url/{image_path}?mimetype={mimetype}&expires_in={expires_in}"
