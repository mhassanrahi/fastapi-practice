from dotenv import load_dotenv
from imagekitio import ImageKit
import os


load_dotenv()

IMAGEKIT_PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY")
if not IMAGEKIT_PRIVATE_KEY:
    raise RuntimeError("Missing required ImageKit environment variables")

imagekit = ImageKit(
    private_key=IMAGEKIT_PRIVATE_KEY,
)
