import abc
import io
import os.path
import uuid
from pathlib import Path
from PIL import Image

# this will be something like ../meme-bot/src/memes
module_path = os.path.dirname(os.path.abspath(__file__))
package_root_dir = str(Path(module_path).parents[1])

class BaseMeme(abc.ABC):

    @abc.abstractmethod
    def image_filename(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def draw_meme(self, image: Image, text: str):
        raise NotImplementedError()

    def generate(self, text):
        meme_unique_image_path = f'{self.image_filename()}-{uuid.uuid4()}.jpg'

        with open(os.path.join(package_root_dir, 'assets', self.image_filename()), 'rb') as f:
            image = Image.open(io.BytesIO(f.read()))
            self.draw_meme(image, text)
            image.save(meme_unique_image_path, format='JPEG')

        return meme_unique_image_path
