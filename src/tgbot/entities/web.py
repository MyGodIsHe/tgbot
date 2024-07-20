from pydantic.dataclasses import dataclass


@dataclass
class AddBalanceRequest:
    user_id: int
    microdollars: int

    @property
    def dollars(self) -> float:
        return self.microdollars / 1_000_000
