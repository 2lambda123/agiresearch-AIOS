import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from aios.hooks.starter import aios_starter
from aios.utils.utils import parse_global_args
from experiment.benchmark.gaia.init_data import REPO_PATH
from pyopenagi.agents.experiment.standard.agent import StandardAgent

DATA_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "gaia",
    "2023",
    "validation"
)

SYSTEM_PROMPT = """You are a general AI assistant. I will ask you a question. Report your thoughts, and finish
your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER].
YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of
numbers and/or strings.
If you are asked for a number, don’t use comma to write your number neither use units such as $ or percent
sign unless specified otherwise.
If you are asked for a string, don’t use articles, neither abbreviations (e.g. for cities), and write the digits in
plain text unless specified otherwise.
If you are asked for a comma separated list, apply the above rules depending of whether the element to be put
in the list is a number or a string.
"""

FILE_PROMPT = """The current task is related to a file, and you may need to read the content of the file first.
The file path is {path}.
"""

FILE_FOLDER = os.path.join(REPO_PATH, "2023", "validation")


class GaiaExpAgent(StandardAgent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def custom_terminate(self) -> bool:
        if self.rounds > 10:
            return True
        return True if "FINAL ANSWER" in self.short_term_memory.last_message()["content"] else False

    def custom_prompt(self) -> str:
        return SYSTEM_PROMPT


def process_one_func(data):
    question = data["Question"]
    if data["file_name"]:
        file_path = FILE_FOLDER + "/" + data["file_name"]
        absolute_path = os.path.abspath(file_path)
        question += ("\n" + FILE_PROMPT.format(path=absolute_path))

    agent = GaiaExpAgent("Standard Agent", question)
    result = agent.run()

    match = re.search(r"FINAL ANSWER:\s*(.*)", result["result"])
    # Extract the content if a match is found
    if match:
        final_answer = match.group(1)
    else:
        final_answer = result["result"]

    prediction = {
        "task_id": data["task_id"],
        "level": data["Level"],
        "result": final_answer
    }
    print(f"Finished Task: \n{prediction}")
    return prediction


def prepare_dataset(task_id: str = None):
    input_file = os.path.join(DATA_PATH, "metadata.jsonl")
    with open(input_file, "r") as file:
        dataset = [json.loads(line) for line in file]

    if task_id is not None:
        for data in dataset:
            if data["task_id"] == task_id:
                return data
    return dataset


def run_infer(outputfile: str, workers: int, level: int, aios_args: dict):
    dataset = prepare_dataset()
    with aios_starter(**aios_args):
        with ThreadPoolExecutor(max_workers=workers) as executor:

            futures = []
            for data in dataset:
                # submit task
                if level and data["Level"] != level:
                    continue

                futures.append(
                    executor.submit(process_one_func, data)
                )

            results = []

            # Obtain infer result
            for future in tqdm(as_completed(futures), total=len(futures), desc="Finished"):
                results.append(future.result())

    # Write result into .jsonl file
    with open(outputfile, "w") as file:
        for line in results:
            json_line = json.dumps(line)
            file.write(json_line + "\n")


def run_infer_specify_task(outputfile: str, task_id: str, aios_args: dict):
    data = prepare_dataset(task_id=task_id)
    with aios_starter(**aios_args):
        result = process_one_func(data)

        # Write result into .jsonl file
        with open(outputfile, "w", encoding="utf-8") as file:
            json_line = json.dumps(result)
            file.write(json_line + "\n")


if __name__ == '__main__':
    parser = parse_global_args()
    parser.add_argument("--output_file", type=str, default="./experiment/benchmark/gaia/predictions.jsonl")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--task_id", type=str, default=None)
    parser.add_argument("--level", type=int, default=None)

    args = parser.parse_args()
    aios_args = {
        "llm_name": args.llm_name,
        "max_gpu_memory": args.max_gpu_memory,
        "eval_device": args.eval_device,
        "max_new_tokens": args.max_new_tokens,
        "scheduler_log_mode": args.scheduler_log_mode,
        "agent_log_mode": args.agent_log_mode,
        "llm_kernel_log_mode": args.llm_kernel_log_mode,
        "use_backend": args.use_backend,
    }

    if args.task_id is not None:
        run_infer_specify_task(
            args.output_file,
            args.task_id,
            aios_args
        )
    else:
        run_infer(
            args.output_file,
            args.workers,
            args.level,
            aios_args
        )
