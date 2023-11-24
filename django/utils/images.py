from io import BytesIO

import numpy as np
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt


def crop_to_circle(input_image):
    # Создаем маску круга с размерами изображения
    mask = Image.new('L', input_image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, input_image.width, input_image.height), fill=255)

    # Обрезаем изображение по маске
    result = Image.new('RGBA', input_image.size, 0)
    result.paste(input_image, mask=mask)

    return result


def create_round_thumbnail(input_image, size=70):
    # Интегрируем обрезку в форму круга
    avatar_circular = crop_to_circle(input_image)

    # Создаем круглую миниатюру
    fig, ax = plt.subplots(figsize=(size/100, size/100), dpi=100)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(plt.Circle((0.5, 0.5), 0.5, color='none', edgecolor='none'))

    # Рисуем обрезанное изображение в центре круга
    ax.imshow(np.array(avatar_circular), extent=(0, 1, 0, 1), transform=ax.transAxes)

    # Убираем оси
    ax.axis('off')

    # Сохраняем миниатюру в байтовый поток
    thumb_io = BytesIO()
    plt.savefig(thumb_io, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close()

    return thumb_io
