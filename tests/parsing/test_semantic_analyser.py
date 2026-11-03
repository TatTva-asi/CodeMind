from app.parsing.python_semantic_analyser import (
    PythonSemanticAnalyzer
)


def test_cross_file_analysis():

    sources = {
        "app/base.py": """
class Animal:
    def speak(self):
        pass
""",

        "app/dog.py": """
from app.base import Animal

class Dog(Animal):
    def bark(self):
        return self.speak()
""",

        "app/main.py": """
from app.dog import Dog

def run():
    dog = Dog()
    dog.bark()
"""
    }

    result = PythonSemanticAnalyzer().analyze(sources)

    # Inheritance
    inheritance = [
        item for item in result.inheritance
        if item.child_class == "Dog"
    ]

    assert len(inheritance) == 1
    assert inheritance[0].status == "resolved"

    # Function call extraction
    calls = [
        item for item in result.calls
        if item.expression == "self.speak"
    ]

    assert len(calls) == 1