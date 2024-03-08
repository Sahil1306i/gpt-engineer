# Generated by CodiumAI
import tempfile

from unittest.mock import MagicMock

import pytest

from langchain.schema import SystemMessage

from gpt_engineer.core.ai import AI
from gpt_engineer.core.prompt import Prompt
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.paths import (
    CODE_GEN_LOG_FILE,
    ENTRYPOINT_FILE,
    ENTRYPOINT_LOG_FILE,
    IMPROVE_LOG_FILE,
    PREPROMPTS_PATH,
)
from gpt_engineer.core.default.steps import (
    curr_fn,
    gen_code,
    gen_entrypoint,
    improve,
    setup_sys_prompt,
    setup_sys_prompt_existing_code,
)
from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.preprompts_holder import PrepromptsHolder

factorial_program = """
To implement a function that calculates the factorial of a number in Python, we will create a simple Python module with a single function `factorial`. The factorial of a non-negative integer `n` is the product of all positive integers less than or equal to `n`. It is denoted by `n!`. The factorial of 0 is defined to be 1.

Let's start by creating the `factorial.py` file which will contain our `factorial` function.

factorial.py
```python
def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    elif n == 0:
        return 1
    else:
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result

if __name__ == "__main__":
import sys

if len(sys.argv) != 2:
    print("Usage: python factorial.py <number>")
    sys.exit(1)

try:
    number = int(sys.argv[1])
    print(f"The factorial of {number} is {factorial(number)}")
except ValueError as e:
    print(e)
    sys.exit(1)
```

Now, let's create a `requirements.txt` file to specify the dependencies for this module. Since we are not using any external libraries, the `requirements.txt` file will be empty, but it's a good practice to include it in Python projects.

requirements.txt
```
# No dependencies required
```
This concludes a fully working implementation.```
"""

factorial_entrypoint = """
Irrelevant explanations
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest test_factorial.py
```
    """


class TestGenCode:
    #  Generates code based on a given prompt using an AI model.
    def test_generates_code_using_ai_model(self):
        # Mock AI class
        class MockAI:
            def start(self, sys_prompt, user_prompt, step_name):
                return [SystemMessage(content=factorial_program)]

        ai = MockAI()
        prompt = Prompt("Write a function that calculates the factorial of a number.")

        memory = DiskMemory(tempfile.mkdtemp())
        preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        code = gen_code(ai, prompt, memory, preprompts_holder)

        assert isinstance(code, FilesDict)
        assert len(code) == 2
        assert CODE_GEN_LOG_FILE in memory
        assert memory[CODE_GEN_LOG_FILE] == factorial_program.strip()

    #  The generated code is saved to disk.
    def test_generated_code_saved_to_disk(self):
        # Mock AI class
        class MockAI:
            def start(self, sys_prompt, user_prompt, step_name):
                return [SystemMessage(content=factorial_program)]

        ai = MockAI()
        prompt = Prompt("Write a function that calculates the factorial of a number.")
        memory = DiskMemory(tempfile.mkdtemp())
        preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        code = gen_code(ai, prompt, memory, preprompts_holder)

        assert isinstance(code, FilesDict)
        assert len(code) == 2
        assert CODE_GEN_LOG_FILE in memory
        assert memory[CODE_GEN_LOG_FILE] == factorial_program.strip()

    #  Raises TypeError if keys are not strings or Path objects.
    def test_raises_type_error_if_keys_not_strings_or_path_objects(self):
        # Mock AI class
        class MockAI:
            def start(self, sys_prompt, user_prompt, step_name):
                return [SystemMessage(content=factorial_program)]

        ai = MockAI()
        prompt = Prompt("Write a function that calculates the factorial of a number.")
        memory = DiskMemory(tempfile.mkdtemp())
        preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        with pytest.raises(TypeError):
            code = gen_code(ai, prompt, memory, preprompts_holder)
            code[123] = "code"

    #  Raises TypeError if values are not strings.
    def test_raises_type_error_if_values_not_strings(self):
        # Mock AI class
        class MockAI:
            def start(self, sys_prompt, user_prompt, step_name):
                return [SystemMessage(content=factorial_program)]

        ai = MockAI()
        prompt = Prompt("Write a function that calculates the factorial of a number.")
        memory = DiskMemory(tempfile.mkdtemp())
        preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        with pytest.raises(TypeError):
            code = gen_code(ai, prompt, memory, preprompts_holder)
            code["file.py"] = 123

    #  Raises KeyError if the file does not exist in the database.
    def test_raises_key_error_if_file_not_exist_in_database(self):
        # Mock AI class
        class MockAI:
            def start(self, sys_prompt, user_prompt, step_name):
                return [SystemMessage(content=factorial_program)]

        ai = MockAI()
        prompt = Prompt("Write a function that calculates the factorial of a number.")
        memory = DiskMemory(tempfile.mkdtemp())
        preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        with pytest.raises(KeyError):
            code = gen_code(ai, prompt, memory, preprompts_holder)
            code["nonexistent_file.py"]


class TestStepUtilities:
    def test_called_from_function(self):
        # Arrange
        def test_function():
            return curr_fn()

        expected_name = "test_function"

        # Act
        actual_name = test_function()

        # Assert
        assert actual_name == expected_name

    def test_constructs_system_prompt_with_predefined_instructions_and_philosophies(
        self,
    ):
        preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        preprompts = preprompts_holder.get_preprompts()
        sys_prompt = setup_sys_prompt(preprompts)
        expected_prompt = (
            preprompts["roadmap"]
            + preprompts["generate"].replace("FILE_FORMAT", preprompts["file_format"])
            + "\nUseful to know:\n"
            + preprompts["philosophy"]
        )
        assert sys_prompt == expected_prompt

    def test_constructs_system_prompt(self):
        preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        preprompts = preprompts_holder.get_preprompts()
        expected_prompt = (
            preprompts["improve"].replace("FILE_FORMAT", preprompts["file_format"])
            + "\nUseful to know:\n"
            + preprompts["philosophy"]
        )
        actual_prompt = setup_sys_prompt_existing_code(preprompts)
        assert actual_prompt == expected_prompt


class TestGenEntrypoint:
    class MockAI:
        def __init__(self, content):
            self.content = content

        def start(self, system, user, step_name):
            return [SystemMessage(content=self.content)]

    #  The function receives valid input and generates a valid entry point script.
    def test_valid_input_generates_valid_entrypoint(self):
        # Mock AI class

        ai_mock = TestGenEntrypoint.MockAI(factorial_entrypoint)
        code = FilesDict()
        tempdir = tempfile.mkdtemp()
        memory = DiskMemory(tempdir)
        # Act
        preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        entrypoint_code = gen_entrypoint(ai_mock, code, memory, preprompts_holder)

        # Assert
        assert ENTRYPOINT_FILE in entrypoint_code
        assert isinstance(entrypoint_code[ENTRYPOINT_FILE], str)
        assert (
            entrypoint_code[ENTRYPOINT_FILE]
            == """python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest test_factorial.py
"""
        )
        assert ENTRYPOINT_LOG_FILE in memory
        assert isinstance(memory[ENTRYPOINT_LOG_FILE], str)
        assert memory[ENTRYPOINT_LOG_FILE] == factorial_entrypoint.strip()

    #  The function receives an empty codebase and returns an empty entry point script.
    def test_empty_codebase_returns_empty_entrypoint(self):
        # Arrange
        ai_mock = TestGenEntrypoint.MockAI("Irrelevant explanation")

        code = FilesDict()
        tempdir = tempfile.mkdtemp()
        memory = DiskMemory(tempdir)

        # Act
        preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        entrypoint_code = gen_entrypoint(ai_mock, code, memory, preprompts_holder)

        # Assert
        assert ENTRYPOINT_FILE in entrypoint_code
        assert isinstance(entrypoint_code[ENTRYPOINT_FILE], str)
        assert entrypoint_code[ENTRYPOINT_FILE] == ""
        assert ENTRYPOINT_LOG_FILE in memory
        assert isinstance(memory[ENTRYPOINT_LOG_FILE], str)
        assert memory[ENTRYPOINT_LOG_FILE] == "Irrelevant explanation"


class TestImprove:
    def test_improve_existing_code(self, tmp_path):
        # Mock the AI class
        ai_patch = """
Some introductory text.
```diff
--- main.py
+++ main.py
@@ -1,1 +1,1 @@
-print('Hello, World!')
+print('Goodbye, World!')
```
"""
        ai_mock = MagicMock(spec=AI)
        ai_mock.next.return_value = [SystemMessage(content=ai_patch)]

        # Create a Code object with existing code
        code = FilesDict(
            {
                "main.py": "print('Hello, World!')",
                "requirements.txt": "numpy==1.18.1",
                "README.md": "This is a sample code repository.",
            }
        )

        # Create a BaseRepository object for memory
        memory = DiskMemory(tmp_path)

        # Define the user prompt
        prompt = Prompt(
            "Change the program to print 'Goodbye, World!' instead of 'Hello, World!'"
        )

        # Call the improve function
        preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        improved_code = improve(ai_mock, prompt, code, memory, preprompts_holder)

        # Assert that the code was improved correctly
        expected_code = FilesDict(
            {
                "main.py": "print('Goodbye, World!')",
                "requirements.txt": "numpy==1.18.1",
                "README.md": "This is a sample code repository.",
            }
        )
        assert improved_code == expected_code

        # Assert that the improvement process was logged in the memory
        assert IMPROVE_LOG_FILE in memory
        assert memory[IMPROVE_LOG_FILE] == ai_patch.strip()
