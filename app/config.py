from pathlib import Path

# Папка, где лежит этот файл (то есть app/)
BASE_DIR = Path(__file__).resolve().parent

# В app/ создается папка media — туда будем сохранять файлы
MEDIA_DIR = BASE_DIR / "media"
