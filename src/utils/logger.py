import click

import os

from datetime import datetime

class BaseLogger:
    def __init__(self,
            logger_name,
            log_mode = "console",
        ) -> None:
        self.logger_name = logger_name
        self.log_mode = log_mode
        self.level_color = dict()

    def log(self, content, level):
        if self.log_mode == "console":
            self.log_to_console(content, level)
        else:
            assert self.log_mode == "file"
            log_file = self.load_log_file()
            self.log_to_file(content, log_file)

    def load_log_file(self):
        pass

    def log_to_console(self, content, level):
        # print(content)
        click.secho(f"[{self.logger_name}] " + content, fg=self.level_color[level])

    def log_to_file(self, content, log_file):
        with open(log_file, "a") as w:
            w.writelines(content)

class SchedulerLogger(BaseLogger):
    def __init__(self, logger_name, log_mode="console") -> None:
        super().__init__(logger_name, log_mode)
        self.level_color = {
            "execute": "green",
            "suspend": "yellow",
            "info": "white"
        }

    def load_log_file(self):
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = os.path.join(os.getcwd(), "logs", "scheduler")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"{date_time}.txt")
        return log_file


class AgentLogger(BaseLogger):
    def __init__(self, logger_name, log_mode="console") -> None:
        super().__init__(logger_name, log_mode)
        self.level_color = {
            "info": "white",
        }

    def load_log_file(self):
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = os.path.join(os.getcwd(), "agents", self.logger_name)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"{date_time}.txt")
        return log_file