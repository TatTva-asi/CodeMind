
from collections import defaultdict
from hashlib import sha256


class SymbolIndex:

    def __init__(self):
        self.symbols = {}
        self.name_index = defaultdict(set)
        self.qualified_name_index = defaultdict(set)
        self.file_index = defaultdict(set)

    @staticmethod
    def generate_symbol_id(file_path, symbol):
        identity = (
            f"{file_path}:"
            f"{symbol.qualified_name}:"
            f"{symbol.kind}"
        )

        return sha256(identity.encode("utf-8")).hexdigest()

    def add_parsed_file(self, parsed_file):

        file_path = parsed_file.file_path

        for symbol in parsed_file.symbols:

            symbol_id = self.generate_symbol_id(
                file_path, symbol
            )

            self.symbols[symbol_id] = symbol

            self.name_index[symbol.name].add(symbol_id)

            self.qualified_name_index[
                symbol.qualified_name
            ].add(symbol_id)

            self.file_index[file_path].add(symbol_id)

    def get_by_id(self, symbol_id):
        return self.symbols.get(symbol_id)

    def get_by_name(self, name):
        return [
            self.symbols[sid]
            for sid in self.name_index.get(name, set())
        ]

    def get_by_qualified_name(self, qualified_name):
        return [
            self.symbols[sid]
            for sid in self.qualified_name_index.get(
                qualified_name, set()
            )
        ]

    def get_by_file(self, file_path):
        return [
            self.symbols[sid]
            for sid in self.file_index.get(file_path, set())
        ]
