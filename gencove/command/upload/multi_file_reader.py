"""File like object that reads multiple files as if they are one file."""
import os


# pylint: disable=R0205
class MultiFileReader(object):
    """File-like object that reads multi-files as if they are one file."""

    def __init__(self, files):
        if isinstance(files, str):
            self._files = (files,)
        else:
            self._files = files

        self._file = None
        self._file_idx = 0
        self._map_sizes = {
            file_path: os.path.getsize(file_path) for file_path in self._files
        }
        self._read_files_offset = {file_path: 0 for file_path in self._files}

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def __iter__(self):  # pylint: disable=E0301
        return self

    def close(self):
        """Close file and clear state."""
        if self._file:
            self._file.close()
            self._file = None
            self._file_idx = 0

    def nextfile(self):
        """Get next file if there is one."""
        prev_file = self._file
        self._file = None
        if prev_file:
            prev_file.close()
            self._file_idx += 1

        try:
            self._file = open(  # pylint: disable=consider-using-with
                self._files[self._file_idx], "rb"
            )
        except IndexError:
            pass

    def filename(self):
        """Returns filename of the current file."""
        return self._file.name

    def fileno(self):
        """Returns fileno of the current file."""
        if self._file:
            try:
                return self._file.fileno()
            except ValueError:
                return -1
        else:
            return -1

    def get_size(self):
        """Returns combined size of the files."""
        return sum(self._map_sizes.values())

    def read(self, size=None):
        """Read a chunk of the file.

        If the size is not provided, will read all files at once.

        Args:
            size (int): number of bytes to read

        Returns:
            bytes: the chunk
        """
        if not size:
            size = self.get_size()

        buf = b""
        while size > 0:
            if not self._file and self._file_idx == len(self._files):
                break

            # pylint: disable=E0012,C0330
            if (
                not self._file
                or self._read_files_offset[self._file.name]
                == self._map_sizes[self._file.name]
            ):
                self.nextfile()
                continue

            unread = (
                self._map_sizes[self._file.name]
                - self._read_files_offset[self._file.name]
            )
            length = min(size, unread)
            self._file.seek(self._read_files_offset[self._file.name])
            buf += self._file.read(length)
            size -= length
            self._read_files_offset[self._file.name] += length

        return buf
