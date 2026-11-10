from typing import Optional

from src.shared.helpers.errors.domain_errors import EntityError


class CreatorLocation:
    """Onde estava quem criou o formulário, no momento da criação.

    É a posição do aparelho, separada do ponto do serviço (`Form.latitude` e
    `Form.longitude`, o pin que a pessoa escolhe no mapa). Junto de
    `created_by` e `created_at`, responde à auditoria: quem criou, o quê e de
    onde.

    - `accuracy`: raio de precisão informado pelo aparelho, em metros.
    - `captured_at`: quando o aparelho mediu a posição (epoch ms) — pode ser
      anterior à criação, se a pessoa demorou no passo do mapa.
    """

    latitude: float
    longitude: float
    accuracy: Optional[float]
    captured_at: Optional[int]

    def __init__(
        self,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None,
        captured_at: Optional[int] = None,
    ):
        if isinstance(latitude, bool) or not isinstance(latitude, (int, float)) or not -90 <= latitude <= 90:
            raise EntityError('Latitude de quem criou deve estar entre -90 e 90')
        if isinstance(longitude, bool) or not isinstance(longitude, (int, float)) or not -180 <= longitude <= 180:
            raise EntityError('Longitude de quem criou deve estar entre -180 e 180')
        if accuracy is not None and (
            isinstance(accuracy, bool) or not isinstance(accuracy, (int, float)) or accuracy < 0
        ):
            raise EntityError('Precisão da localização de quem criou deve ser um número não negativo')
        if captured_at is not None and (
            isinstance(captured_at, bool) or not isinstance(captured_at, int) or captured_at < 0
        ):
            raise EntityError('Momento da localização de quem criou deve ser um timestamp inteiro')
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.accuracy = float(accuracy) if accuracy is not None else None
        self.captured_at = captured_at

    def to_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "captured_at": self.captured_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "CreatorLocation":
        accuracy = data.get("accuracy")
        captured_at = data.get("captured_at")
        return CreatorLocation(
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            accuracy=float(accuracy) if accuracy is not None else None,
            captured_at=int(captured_at) if captured_at is not None else None,
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, CreatorLocation) and self.to_dict() == other.to_dict()

    def __repr__(self) -> str:
        return f"CreatorLocation({self.to_dict()!r})"
