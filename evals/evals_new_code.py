import os
import subprocess

from datetime import datetime
from pathlib import Path

from eval_tools import load_evaluations_from_file, to_emoji, check_evaluation_component
from gpt_engineer.db import DB

def single_evaluate(eval_ob: dict) -> list[bool]:
    """Evaluates a single prompt for creating a new project."""
    print(f"running evaluation: {eval_ob['name']}")

    workspace = DB(eval_ob["project_root"])
    base_abs = Path(os.getcwd())
    code_base_abs = base_abs / eval_ob["project_root"]

    # write to the consent file so we don't get a prompt that hangs
    consent_file = base_abs / ".gpte_consent"
    consent_file.write_text("true")

    # Step 1. Setup known project
    # write the folder and prompt file

    print(f"prompt: {eval_ob['code_prompt']}")
    prompt_path = code_base_abs / 'prompt'
    workspace[prompt_path] = f"{eval_ob['code_prompt']}\n"

    # # Step 2. Run gpt-engineer 
    # log_path = code_base_abs / "log.txt"
    # log_file = open(log_path, "w")
    # process = subprocess.Popen(
    #     [
    #         "python",
    #         "-u",  # Unbuffered output
    #         "-m",
    #         "gpt_engineer.main",
    #         eval_ob["project_root"],
    #         "--steps",
    #         "eval_new_code",
    #     ],
    #     stdout=log_file,
    #     stderr=log_file,
    #     bufsize=0,
    # )
    # print(f"waiting for {eval_ob['name']} to finish.")
    # process.wait()  # we want to wait until it finishes.

    print("running tests on the newly generated code")
    # TODO: test the code we should have an executable name
    evaluation_results = []
    for test_case in eval_ob["expected_results"]:
        print(f"checking: {test_case['type']}")
        test_case["project_root"] = Path(eval_ob["project_root"])
        evaluation_results.append(check_evaluation_component(test_case))

    return evaluation_results


def generate_report(evals: list[dict], res: list[list[bool]]) -> None:
    pass # TODO: modify the code from existing code evals.  


def run_all_evaluations(eval_list: list[dict]) -> None:
    results = []
    for eval_ob in eval_list:
        results.append(single_evaluate(eval_ob))

    # Step 4. Generate Report
    generate_report(eval_list, results)

if __name__ == "__main__":
    eval_list = load_evaluations_from_file("evals/new_code_eval.yaml")
    run_all_evaluations(eval_list)