from ..defaults import AppDefaults


class AppleBooksDefaults:

    name = "applebooks"
    version = "Books v1.19 (1645)"

    # applebooks data
    src_root_dir = (
        AppDefaults.home / "Library/Containers/com.apple.iBooksX/Data/Documents"
    )
    src_bklibrary_dir = src_root_dir / "BKLibrary"
    src_aeannotation_dir = src_root_dir / "AEAnnotation"

    # local data
    local_root_dir = AppDefaults.day_dir / "applebooks"
    local_db_dir = local_root_dir / "db"
    local_bklibrary_dir = local_db_dir / "BKLibrary"
    local_aeannotation_dir = local_db_dir / "AEAnnotation"
    sources_json = local_root_dir / "sources.json"
    annotations_json = local_root_dir / "annotations.json"

    # misc
    ns_time_interval_since_1970 = 978307200.0
