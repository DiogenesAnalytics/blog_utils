"""Displaying images in Jupyter notebooks."""

import base64
from io import BytesIO
from typing import Iterable
from typing import List
from typing import Sequence
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from .transform import crop_to_target


def display_images_in_grid(
    images: Sequence[Image.Image],  # Iterable of PIL Image objects
    titles: List[str],
    target_size: Tuple[int, int],
    rows: int,
    bottom_title: str,
    bottom_title_coords: Tuple[float, float] = (0.5, 0.15),
    ax_title_y_coord: float = -0.15,
    fig_size: Tuple[int, int] = (5, 5),
    bg_color: str = "#181818",
) -> None:
    """Display images in a grid using matplotlib."""
    # get some initial info
    num_images: int = len(images)
    cols: int = num_images // rows + (
        num_images % rows > 0
    )  # Calculate number of columns

    # create the subplots grid
    fig, axs = plt.subplots(nrows=rows, ncols=cols, figsize=fig_size)

    # set the background color of the figure and axes
    fig.patch.set_facecolor(bg_color)

    # flatten axs if there is only one row or column
    if isinstance(axs, np.ndarray):
        for ax in axs.flat:
            ax.set_facecolor(bg_color)
        axs = np.ravel(axs)
    else:
        axs = [axs]

    # loop through each image, resize, and display
    for i, ax in enumerate(axs):
        # ensure we don't go out of bounds
        if i < num_images:
            image = images[i]
            # resize the image while preserving the aspect ratio and cropping
            image = crop_to_target(image, target_size)

            # determine colormap based on image mode
            if image.mode == "RGB":
                ax.imshow(image)
            else:
                ax.imshow(image, cmap="gray")

            # set the subtitle (title) for each image
            if i < len(titles):
                ax.set_title(titles[i], color="white", y=ax_title_y_coord)

            # turn off axis for cleaner display
            ax.axis("off")
        else:
            # hide empty subplots
            ax.axis("off")

    # add a bottom title if provided
    if bottom_title:
        fig.text(
            *bottom_title_coords,  # Center the text at the bottom
            bottom_title,
            ha="center",
            color="white",
        )

    # adjust layout for better spacing between images
    plt.tight_layout()
    plt.show()


def display_base64_images_grid(
    encoded_images: Iterable[str],
    titles: List[str],
    target_size: Tuple[int, int],
    rows: int,
    bottom_title: str,
    bottom_title_coords: Tuple[float, float] = (0.5, 0.15),
    ax_title_y_coord: float = -0.15,
    fig_size: Tuple[int, int] = (5, 5),
    bg_color: str = "#181818",
) -> None:
    """Display base64 decoded images in a grid using matplotlib."""
    # decode base64 images
    images = [Image.open(BytesIO(base64.b64decode(img))) for img in encoded_images]

    # call the core function with the decoded images
    display_images_in_grid(
        images=images,
        titles=titles,
        target_size=target_size,
        rows=rows,
        bottom_title=bottom_title,
        bottom_title_coords=bottom_title_coords,
        ax_title_y_coord=ax_title_y_coord,
        fig_size=fig_size,
        bg_color=bg_color,
    )
