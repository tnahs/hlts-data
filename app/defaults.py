from pathlib import Path
from datetime import datetime


class AppDefaults:

    home = Path.home()
    date = datetime.now().strftime("%Y-%m-%d")

    name = "hltsdump"

    root_dir = home / ".hltsdump"
    config_file = root_dir / "config.json"

    day_dir = root_dir / date
