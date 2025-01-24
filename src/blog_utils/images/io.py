"""IO functions for images."""

import os
from pathlib import Path
from typing import Generator
from typing import List
from typing import Tuple
from typing import Union

from PIL import Image


def validate_image_file(file_path: Path) -> bool:
    """Validate if the given path is a valid image file."""
    try:
        with Image.open(file_path) as img:
            img.verify()  # Verify the file is a valid image
        return True
    except (IOError, SyntaxError):
        return False


def open_image_file(filepath: Union[str, Path]) -> Image.Image:
    """Opens an image file and returns a PIL Image object."""
    path = Path(filepath)
    if not validate_image_file(path):
        raise ValueError(f"The file {filepath} is not a valid image.")
    return Image.open(path)


def open_images_in_directory(
    directory: Union[str, Path]
) -> Generator[Image.Image, None, None]:
    """Yields PIL Image objects for images in a directory and its subdirectories."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise ValueError(f"The path {directory} is not a valid directory.")

    for file in dir_path.rglob("*"):
        if file.is_file() and validate_image_file(file):
            yield open_image_file(file)


def get_image_count_in_directory(dir_path: Path) -> int:
    """Count the number of valid image files in the directory and its subdirectories."""
    image_count = 0
    for file in dir_path.rglob("*"):
        if file.is_file() and validate_image_file(file):
            image_count += 1
    return image_count


def input_path(prompt: str, is_file: bool = True, test_mode: bool = False) -> Path:
    """Prompt user to input a valid file or directory path."""
    # setup attempt counter/limits
    attempt = 0
    max_attempts = 3

    # loop
    while True:
        path = Path(input(prompt).strip())
        if is_file and path.is_file():
            return path
        elif not is_file and path.is_dir():
            return path
        else:
            print(
                f"The path is not a valid {'file' if is_file else 'directory'}."
                " Please try again."
            )

        # increment attempt count and check if we reached max attempts
        attempt += 1
        if test_mode and attempt >= max_attempts:
            raise ValueError("Max attempts reached. Invalid path input.")


def input_image_path(test_mode: bool = False) -> str:
    """Interactively get a valid image file path."""
    while True:
        image_path = input_path(
            "Enter the path to the image file: ",
            is_file=True,
            test_mode=test_mode,
        )
        if validate_image_file(image_path):
            print("Image successfully verified!")
            return str(image_path)
        print("The file is not a valid image. Please try again.")


def input_image_dir(test_mode: bool = False) -> str:
    """Interactively get a directory containing valid image files."""
    while True:
        dir_path = input_path(
            "Enter the path to the image(s) directory: ",
            is_file=False,
            test_mode=test_mode,
        )
        image_count = get_image_count_in_directory(dir_path)
        if image_count > 0:
            print(
                f"Found {image_count} valid image(s) in directory"
                f" and its subdirectories: {dir_path}"
            )
            return str(dir_path)
        print("No valid images found in the directory. Please try again.")


def save_image_file(img: Image.Image, filepath: str, format: str = "JPEG") -> None:
    """Saves a PIL Image object to a file."""
    img.save(filepath, format=format)


def save_images_to_directory(
    images: List[Image.Image], directory: str, format: str = "JPEG"
) -> None:
    """Saves a list of PIL Image objects to a directory."""
    os.makedirs(directory, exist_ok=True)
    for i, img in enumerate(images):
        filepath = os.path.join(directory, f"image_{i}.{format.lower()}")
        save_image_file(img, filepath, format=format)


def convert_size(size_in_bytes: int, unit: str) -> float:
    """Converts file size from bytes to the specified unit."""
    # define conversion functions
    unit_factors = {
        "bytes": 1,
        "KB": 1024,
        "MB": 1024**2,
    }

    # raise error
    if unit not in unit_factors:
        raise ValueError(f"Invalid unit {unit!r}. Choose from 'bytes', 'KB', or 'MB'.")

    # calculate size for unit
    return size_in_bytes / unit_factors[unit]


def list_file_sizes(
    directory: str, units: str = "KB"
) -> Generator[Tuple[str, float], None, None]:
    """Lists the sizes of all files in the specified directory."""
    # get path obj
    directory_path = Path(directory)

    # yield file sizes
    for file in directory_path.iterdir():
        if file.is_file():
            yield (file.name, convert_size(file.stat().st_size, units))


def print_file_sizes(directory: str, unit: str = "KB") -> None:
    """Prints the sizes of all files directory."""
    # call list_file_sizes and print the results
    for filename, size in list_file_sizes(directory, unit):
        print(f"{filename}: {size:.2f} {unit}")
