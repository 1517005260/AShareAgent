import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO


class OutputLogger:
    """
    A class that redirects stdout to both console and file.
    """

    def __init__(self, filename: str | None = None):
        """
        Initialize the output logger.

        Args:
            filename: Optional filename to save the output. If None, a timestamp-based filename will be used.
        """
        self.terminal = sys.stdout
        if filename is None:
            # Create logs directory if it doesn't exist
            Path("logs").mkdir(exist_ok=True)
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/output_{timestamp}.txt"

        self.log_file: TextIO = open(filename, "w", encoding='utf-8')
        self.filename = filename

    def write(self, message: str) -> None:
        """Write to both terminal and file."""
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()  # Ensure immediate writing to file

    def flush(self) -> None:
        """Flush both outputs."""
        self.terminal.flush()
        self.log_file.flush()

    def __del__(self) -> None:
        """Clean up by closing the log file."""
        if hasattr(self, 'log_file'):
            self.log_file.close()