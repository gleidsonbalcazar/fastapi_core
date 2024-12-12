from abc import ABC, abstractmethod


class EmailPort(ABC):
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str):
        pass

    @abstractmethod
    async def send_pin(self, to: str, pin: str, tenant: str, msg: str):
        pass

    @abstractmethod
    async def send_email_recovery(self, to: str, tenant: str, msg: str):
        pass
