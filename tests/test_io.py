"""Tests for blog_utils.images.io module."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator
from typing import Tuple

import pytest
from PIL import Image
from pytest import MonkeyPatch

from blog_utils.images.io import input_image_dir
from blog_utils.images.io import input_image_path
from blog_utils.images.io import open_image_file
from blog_utils.images.io import open_images_in_directory
from blog_utils.images.io import validate_image_file


@pytest.fixture(scope="function")
def temp_dir_with_images() -> Generator[Tuple[Path, Path, Path], None, None]:
    """Fixture to create a temporary directory with test files."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # create a valid image file
        valid_image = temp_path / "test_image.jpg"
        with Image.new("RGB", (10, 10)) as img:
            img.save(valid_image)

        # create an invalid file
        invalid_file = temp_path / "invalid_file.txt"
        invalid_file.write_text("This is not an image.")

        yield temp_path, valid_image, invalid_file


def test_input_image_path_invalid_path(monkeypatch: MonkeyPatch) -> None:
    """Test input_image_path with a non-existent path."""
    monkeypatch.setattr("builtins.input", lambda _: "/non/existent/path")
    with pytest.raises(ValueError):
        input_image_path(test_mode=True)


def test_input_image_path_valid(
    temp_dir_with_images: Tuple[Path, Path, Path], monkeypatch: MonkeyPatch
) -> None:
    """Test input_image_path with a valid image file."""
    temp_path, valid_image, _ = temp_dir_with_images

    monkeypatch.setattr("builtins.input", lambda _: str(valid_image))
    result = input_image_path(test_mode=True)
    assert result == str(valid_image)


def test_validate_image_file_invalid_file(
    temp_dir_with_images: Tuple[Path, Path, Path], monkeypatch: MonkeyPatch
) -> None:
    """Test input_image_path with an invalid file."""
    temp_path, _, invalid_file = temp_dir_with_images

    monkeypatch.setattr("builtins.input", lambda _: str(invalid_file))
    assert not validate_image_file(invalid_file)


def test_input_image_dir_valid(
    temp_dir_with_images: Tuple[Path, Path, Path], monkeypatch: MonkeyPatch
) -> None:
    """Test input_image_dir with a valid directory containing images."""
    temp_path, valid_image, _ = temp_dir_with_images

    monkeypatch.setattr("builtins.input", lambda _: str(temp_path))
    result = input_image_dir(test_mode=True)
    assert result == str(temp_path)


def test_open_image_file_invalid_image(
    temp_dir_with_images: Tuple[Path, Path, Path]
) -> None:
    """Test open_image_file with an invalid image."""
    temp_path, _, invalid_file = temp_dir_with_images

    # should raise a ValueError
    with pytest.raises(ValueError):
        open_image_file(invalid_file)


def test_open_images_in_directory_valid_images(
    temp_dir_with_images: Tuple[Path, Path, Path]
) -> None:
    """Test open_images_in_directory with valid image files."""
    temp_path, valid_image, _ = temp_dir_with_images

    # create the directory where images will be checked
    images = list(open_images_in_directory(temp_path))

    # only the valid image should be yielded
    assert len(images) == 1

    # ensure it is an Image object
    assert isinstance(images[0], Image.Image)
