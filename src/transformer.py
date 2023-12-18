from abc import abstractmethod


class Transformer:
    @abstractmethod
    def prepare_transform(self, filenames: list[str]) -> list[str]:
        raise NotImplementedError()

    @abstractmethod
    def transform(self, filename: str) -> str:
        raise NotImplementedError()
