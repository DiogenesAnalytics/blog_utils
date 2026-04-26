"""Transform images (e.g. resize, crop, etc)."""

import io
import warnings
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import Optional
from typing import Tuple

import cv2
import numpy as np
from PIL import Image

from .io import open_image_file
from .io import open_images_in_directory


def shrink_image_to_size(
    img: Image.Image,
    target_size_kb: int,
    initial_quality: int = 95,
    min_quality: int = 10,
    reduction_factor: float = 0.9,
    quality_step: int = 5,
    resize_step_factor: float = 0.95,
) -> Image.Image:
    """Shrinks the image to approximate target size."""
    # convert the image to RGB mode if it's not already
    if img.mode != "RGB":
        img = img.convert("RGB")

    # initialize img_resized with the original image
    img_resized = img

    # begin size reduction loop
    while initial_quality >= min_quality:
        # resize the image based on the reduction factor
        width, height = img.size
        img_resized = img.resize(
            (int(width * reduction_factor), int(height * reduction_factor)),
            Image.Resampling.LANCZOS,
        )

        # use a context manager to handle the BytesIO object
        with io.BytesIO() as output_stream:
            # save to memory buffer
            img_resized.save(output_stream, "JPEG", quality=initial_quality)

            # check image size (in kilobytes)
            file_size_kb: float = len(output_stream.getvalue()) / 1024

            # break the loop if the file size is within the desired range
            if file_size_kb <= target_size_kb:
                return img_resized

        # if not, reduce quality and try again
        initial_quality -= quality_step
        reduction_factor *= resize_step_factor

    # issue a warning if the target size could not be met
    warnings.warn(
        "Unable to reduce image below target size without significant quality loss.",
        UserWarning,
        stacklevel=2,
    )

    # return the last attempted image if the loop ends without meeting the target size
    return img_resized


def shrink_image_at_filepath(
    input_path: str, target_size_kb: int, **kwargs: Any
) -> Image.Image:
    """Shrinks the image at the given file path."""
    # open the image from the file path
    img: Image.Image = open_image_file(input_path)

    # shrink the image
    return shrink_image_to_size(img, target_size_kb, **kwargs)


def shrink_images_in_directory(
    directory: str, target_size_kb: int, **kwargs: Any
) -> Generator[Image.Image, None, None]:
    """Yields resized images from a directory."""
    # Use the image_io module to open images from the directory
    for img in open_images_in_directory(directory):
        # Shrink image and yield the resized image
        yield shrink_image_to_size(img, target_size_kb, **kwargs)


def crop_to_target(image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
    """Crop the image to fit the target size from the top down."""
    # get current images width/height
    width, height = image.size

    # get corresponding target width/height
    target_width, target_height = target_size

    # resize image with aspect ratio preservation
    if width / height > target_width / target_height:
        new_height = target_height
        new_width = int((width / height) * new_height)
    else:
        new_width = target_width
        new_height = int((height / width) * new_width)

    # now apply resize
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # ensure image is in RGB format for further processing
    if image.mode != "RGB":
        image = image.convert("RGB")

    # calculate cropping box from the top
    left = (new_width - target_width) / 2
    top = 0
    right = (new_width + target_width) / 2
    bottom = target_height

    # ensure cropping box is within image bounds
    if right > new_width:
        right = new_width
        left = right - target_width
    if bottom > new_height:
        bottom = new_height
        top = bottom - target_height

    # convert cropping box coordinates to integers
    left = int(left)
    top = int(top)
    right = int(right)
    bottom = int(bottom)

    # crop and final resize
    image = image.crop((left, top, right, bottom))
    image = image.resize(target_size, Image.Resampling.LANCZOS)

    # voila
    return image


def validate_kernel_size(kernel_size: int) -> None:
    """Validate that kernel_size is a positive odd integer."""
    if kernel_size <= 0:
        raise ValueError("kernel_size must be a positive integer.")
    if kernel_size % 2 == 0:
        raise ValueError("kernel_size must be an odd number.")


def irreversible_blur(
    img: Image.Image,
    downscale_factor: float = 1.0,
    kernel_size: int = 51,
    noise_intensity: int = 25,
) -> Image.Image:
    """Apply irreversible blurring to an image."""
    # make sure kernel_size is correct
    validate_kernel_size(kernel_size)

    # convert the PIL image to a NumPy array (for OpenCV processing)
    img_cv = np.array(img)
    if img_cv.ndim == 2:  # Grayscale image
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_GRAY2BGR)

    # apply shrink/resize to pixelate
    height, width = img_cv.shape[:2]
    small_img = cv2.resize(
        img_cv,
        (int(width * downscale_factor), int(height * downscale_factor)),
        interpolation=cv2.INTER_LINEAR,
    )
    pixelated_img = cv2.resize(
        small_img, (width, height), interpolation=cv2.INTER_NEAREST
    )

    # apply gaussian blur
    blurred_img = cv2.GaussianBlur(pixelated_img, (kernel_size, kernel_size), 0)

    # sprinkle in some pepper for extra seasoning
    noise = np.random.normal(0, noise_intensity, blurred_img.shape)
    noisy_img = blurred_img.astype(np.float32) + noise

    # clip the values to ensure they are in the valid range
    noisy_img = np.clip(noisy_img, 0, 255)

    # convert back to PIL Image and save it
    blurred_pil_img = Image.fromarray(noisy_img.astype(np.uint8))

    # irreversible blur complete
    return blurred_pil_img


def blur_multi_images(
    images: Iterable[Image.Image],
    blur_method: Callable[[Image.Image], Image.Image] = irreversible_blur,
    blur_params: Optional[Dict[str, Any]] = None,
) -> Generator[Image.Image, None, None]:
    """Apply a blur method to a sequence of PIL Image.Image objects."""
    # The parameters for blurring
    blur_params = {} if blur_params is None else blur_params

    # Call the blur_method with image and params
    for img in images:
        yield blur_method(img, **blur_params)
