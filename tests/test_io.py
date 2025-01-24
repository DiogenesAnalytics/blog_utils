"""Tests for blog_utils.images.io module."""

from pathlib import Path
from typing import Generator
from typing import Tuple

import pytest
from PIL import Image
from pytest import MonkeyPatch

from blog_utils.images.io import convert_size
from blog_utils.images.io import get_image_count_in_directory
from blog_utils.images.io import input_image_dir
from blog_utils.images.io import input_image_path
from blog_utils.images.io import list_file_sizes
from blog_utils.images.io import open_image_file
from blog_utils.images.io import open_images_in_directory
from blog_utils.images.io import save_image_file
from blog_utils.images.io import save_images_to_directory
from blog_utils.images.io import validate_and_standardize_extension
from blog_utils.images.io import validate_image_file


@pytest.fixture(scope="function")
def temp_dir_with_images(
    tmp_path: Path,
) -> Generator[Tuple[Path, Path, Path, Path], None, None]:
    """Fixture to create a temp dire with test files, including a subdir."""
    # create a valid image file in the root directory
    valid_image = tmp_path / "test_image.jpg"
    with Image.new("RGB", (10, 10)) as img:
        img.save(valid_image)

    # create an invalid file in the root directory
    invalid_file = tmp_path / "invalid_file.txt"
    invalid_file.write_text("This is not an image.")

    # create a subdirectory
    sub_dir = tmp_path / "subdir"
    sub_dir.mkdir()

    # create a valid image file in the subdirectory
    sub_dir_image = sub_dir / "subdir_image.jpg"
    with Image.new("RGB", (10, 10)) as img:
        img.save(sub_dir_image)

    yield tmp_path, valid_image, invalid_file, sub_dir_image


def test_get_image_count_in_directory(
    temp_dir_with_images: Tuple[Path, Path, Path, Path]
) -> None:
    """Test get_image_count_in_directory with image/non-image files."""
    # unpack the fixture
    temp_path, *_ = temp_dir_with_images

    # count images in the directory, including subdirectories
    result = get_image_count_in_directory(temp_path)

    # expect 2 valid images (one in the root and one in the subdirectory)
    assert result == 2


def test_validate_image_file(
    temp_dir_with_images: Tuple[Path, Path, Path, Path], monkeypatch: MonkeyPatch
) -> None:
    """Test validate_image_file with valid/invalid paths."""
    # unpack fixture
    _, valid_image, invalid_file, _ = temp_dir_with_images

    # check validation of image/non-image files works
    assert validate_image_file(valid_image)
    assert not validate_image_file(invalid_file)


def test_input_image_path_invalid_path(monkeypatch: MonkeyPatch) -> None:
    """Test input_image_path with a non-existent path."""
    # mock input
    monkeypatch.setattr("builtins.input", lambda _: "/non/existent/path")

    # expect exception on invalid path
    with pytest.raises(ValueError):
        input_image_path(test_mode=True)


def test_input_image_path_valid(
    temp_dir_with_images: Tuple[Path, Path, Path, Path], monkeypatch: MonkeyPatch
) -> None:
    """Test input_image_path with a valid image file."""
    # unpack fixture
    _, valid_image, *_ = temp_dir_with_images

    # mock input
    monkeypatch.setattr("builtins.input", lambda _: str(valid_image))

    # get input
    result = input_image_path(test_mode=True)

    # check
    assert result == str(valid_image)


def test_input_image_dir_valid(
    temp_dir_with_images: Tuple[Path, Path, Path, Path], monkeypatch: MonkeyPatch
) -> None:
    """Test input_image_dir with a valid directory containing images."""
    # unpack fixture
    temp_path, *_ = temp_dir_with_images

    # mock input
    monkeypatch.setattr("builtins.input", lambda _: str(temp_path))

    # get input
    result = input_image_dir(test_mode=True)

    # check
    assert result == str(temp_path)


def test_open_image_file_invalid_image(
    temp_dir_with_images: Tuple[Path, Path, Path, Path]
) -> None:
    """Test open_image_file with an invalid image."""
    # unpack fixture
    *_, invalid_file, _ = temp_dir_with_images

    # expect an exception
    with pytest.raises(ValueError):
        open_image_file(invalid_file)


def test_open_image_file_corrupted(
    temp_dir_with_images: Tuple[Path, Path, Path, Path]
) -> None:
    """Test open_image_file with corrupted file."""
    # unpack fixture
    temp_path, *_ = temp_dir_with_images

    # create a corrupted image file
    corrupted_file = temp_path / "corrupted_image.jpg"
    corrupted_file.write_bytes(b"This is not a valid image format")

    # assert corrupted image raises ValueError
    with pytest.raises(ValueError):
        open_image_file(corrupted_file)


def test_open_images_in_directory_valid_images(
    temp_dir_with_images: Tuple[Path, Path, Path, Path]
) -> None:
    """Test open_images_in_directory with valid image files."""
    # unpack fixture
    temp_path, *_ = temp_dir_with_images

    # populate lists with all images found (including in subdirs)
    images = list(open_images_in_directory(temp_path))

    # only the valid image should be yielded
    assert len(images) == 2

    # ensure it is an Image object
    assert isinstance(images[0], Image.Image)
    assert isinstance(images[1], Image.Image)


def test_open_images_in_directory_empty_directory(
    temp_dir_with_images: Tuple[Path, Path, Path, Path]
) -> None:
    """Test open_images_in_directory with an empty directory."""
    # unpack fixture
    temp_path, *_ = temp_dir_with_images

    # remove all files and subdirectories recursively
    for item in temp_path.rglob("*"):
        # remove files
        if item.is_file():
            item.unlink()

    # open the images (should be none)
    images = list(open_images_in_directory(temp_path))

    # check
    assert len(images) == 0


def test_validate_and_standardize_extension_valid() -> None:
    """Test validate_and_standardize_extension with valid extensions."""
    # test with leading dot
    assert validate_and_standardize_extension(".jpg") == (".jpg", "JPEG")

    # test without leading dot
    assert validate_and_standardize_extension("png") == (".png", "PNG")

    # test with upper case
    assert validate_and_standardize_extension("WEBP") == (".webp", "WEBP")


def test_validate_and_standardize_extension_invalid() -> None:
    """Test validate_and_standardize_extension with invalid extensions."""
    # test with leading dot
    with pytest.raises(ValueError):
        validate_and_standardize_extension(".foo_bar_baz")

    # test without leading dot
    with pytest.raises(ValueError):
        validate_and_standardize_extension("foo_bar_baz")


def test_save_image_file(temp_dir_with_images: Tuple[Path, Path, Path, Path]) -> None:
    """Test save_image_file for saving an image."""
    # unpack fixture
    _, valid_image, *_ = temp_dir_with_images

    # create a save path
    save_path = valid_image.parent / "saved_image.jpg"

    # open the valid image and save it to the new path
    img = open_image_file(valid_image)
    save_image_file(img, str(save_path))

    # check that the file exists
    assert save_path.is_file()

    # check that it is a valid image
    assert validate_image_file(save_path)


def test_save_images_to_directory(
    temp_dir_with_images: Tuple[Path, Path, Path, Path]
) -> None:
    """Test save_images_to_directory for saving multiple images."""
    # unpack fixture
    temp_path, valid_image, *_ = temp_dir_with_images

    # create the save directory
    save_dir = temp_path / "saved_images"
    save_dir.mkdir()

    # save multiple images
    img = open_image_file(valid_image)
    save_images_to_directory([img, img], str(save_dir))

    # check that two images are saved
    saved_images = list(save_dir.glob("*.jpg"))
    assert len(saved_images) == 2

    # validate the saved images
    assert all(validate_image_file(img) for img in saved_images)


def test_convert_size() -> None:
    """Test convert_size for valid and invalid conversions."""
    # Test valid conversions
    assert convert_size(1024, "KB") == 1.0
    assert convert_size(1024**2, "MB") == 1.0
    assert convert_size(1, "bytes") == 1.0

    # Test invalid unit
    with pytest.raises(ValueError):
        convert_size(1024, "GB")


def test_list_file_sizes(temp_dir_with_images: Tuple[Path, Path, Path, Path]) -> None:
    """Test list_file_sizes correct sizes and files."""
    # unpack fixture
    temp_path, valid_image, invalid_file, sub_dir_image = temp_dir_with_images

    # list file sizes
    file_sizes = list(list_file_sizes(temp_path, "KB"))

    # expected file sizes (using relative paths)
    expected_files = {
        valid_image.relative_to(temp_path): valid_image.stat().st_size / 1024,
        invalid_file.relative_to(temp_path): invalid_file.stat().st_size / 1024,
        sub_dir_image.relative_to(temp_path): sub_dir_image.stat().st_size / 1024,
    }

    # check the number of files
    assert len(file_sizes) == len(expected_files)

    # validate file names and sizes
    for file_name, size in file_sizes:
        # convert file_name back to a Path for relative comparison
        assert Path(file_name) in expected_files
        assert pytest.approx(size, rel=1e-3) == expected_files[Path(file_name)]
