# define relationsip type and semantics
from enum import Enum

class RelationshipType(str, Enum):

    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"