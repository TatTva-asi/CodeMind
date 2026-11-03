# define relationsip type and semanticsfrom enum import Enum
import Enum

class RelationshipType(str, Enum):

    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"