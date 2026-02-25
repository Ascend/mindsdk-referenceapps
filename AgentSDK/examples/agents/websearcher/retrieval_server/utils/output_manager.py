"""
Copyright 2026 Huawei Technologies Co., Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
import threading
import traceback

class OutputQueueHandler:
    """
    Redirects stdout/stderr output to a multiprocessing queue
    
    Captures all print statements and error messages from subprocesses,
    formats them with metadata (port, pid), and sends to a shared queue
    for centralized logging and monitoring.
    """
    def __init__(self, queue, port, pid):
        """
        Initialize the output handler
        
        Args:
            queue: Queue object to receive output messages
            port: Network port number where the process is listening
            pid: Process ID assigned by the system
        """
        self.queue = queue
        self.port = port
        self.pid = pid
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def __enter__(self):
        """Context manager entry point"""
        sys.stdout = self
        sys.stderr = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        if exc_type:
            traceback_str = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb))
            self.queue.put({
                "type": "error",
                "port": self.port,
                "pid": self.pid,
                "message": traceback_str
            })

    def write(self, message):
        """Redirect output to the message queue"""
        if message.strip():
            self.queue.put({
                "type": "stdout",
                "port": self.port,
                "pid": self.pid,
                "message": message.rstrip()
            })

    def flush(self):
        """Compatibility method for flush operation"""
        pass

    def isatty(self):
        """
        Check if output is a terminal
        
        Returns:
            The original stdout's isatty status if available
        """
        return self.original_stdout.isatty() if hasattr(self.original_stdout, 'isatty') else False


class OutputLogger(threading.Thread):
    """
    Thread class for handling and printing subprocess output from a queue.
    
    This daemon thread continuously retrieves log records from a queue and formats
    them with process identifiers before printing to stdout.
    """
    def __init__(self, queue):
        """
        Initializes the OutputLogger with the given queue.

        Args:
            queue: Queue object for inter-process communication.
        """
        super().__init__()
        self.queue = queue
        self.daemon = True

    def run(self):
        """
        Main thread loop that processes log records.

        Continuously retrieves records from the queue, formats them, and prints to stdout.
        Exits when a None termination signal is received.
        """
        while True:
            try:
                record = self.queue.get()
                if record is None:
                    break
                format_log_message = f"[Backend {record['port']} (PID: {record['pid']})] {record['message']}"
                print(format_log_message)
                sys.stdout.flush()
            except KeyError as e:
                print(f"Invalid log format: {e}")
            except Exception as e:
                print(f"Log handler error: {e}")
