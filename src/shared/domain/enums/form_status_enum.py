from enum import Enum


class FormStatus(Enum):
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    SENT = 'SENT'
    CANCELLED = 'CANCELLED'
