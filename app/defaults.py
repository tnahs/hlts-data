from datetime import datetime
from pathlib import Path


class AppDefaults:

    home = Path.home()
    date = datetime.now().strftime("%Y-%m-%d")

    name = "hlts-data"

    root_dir = home / ".hlts-data"
    config_file = root_dir / "config.json"

    day_dir = root_dir / date
