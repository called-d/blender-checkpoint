import os
import json
import uuid
import shutil

import re
from unicodedata import normalize

from datetime import datetime, timezone

from . import config


# Format: Fri Sep  2 19:36:07 2022 +0530
CP_TIME_FORMAT = "%c %z"


def slugify(text):
    """
    Simplifies a string, converts it to lowercase, removes non-word characters
    and spaces, converts spaces and apostrophes to hyphens.
    """
    text = normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    text = re.sub(r'[^\w\s\'-]', '', text).strip().lower()
    text = re.sub(r'[-\s\'"]+', '-', text)
    return text


def _get_disk_usage(filepath):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(filepath):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


def getLastModifiedStr(date):
    """
    Returns last modified string
    date: offset-aware datetime.datetime object
    """

    # Get time difference
    now = datetime.now(timezone.utc)
    delta = now - date

    output = ""

    days = delta.days
    if days <= 0:
        hours = delta.seconds // 3600
        if hours <= 0:
            mins = (delta.seconds // 60) % 60
            if mins <= 0:
                secs = delta.seconds - hours * 3600 - mins * 60
                if secs <= 0:
                    output = "now"

                # Secs
                elif secs == 1:
                    output = f"{secs} sec"
                else:
                    output = f"{secs} sec"

            # Mins
            elif mins == 1:
                output = f"{mins} min"
            else:
                output = f"{mins} mins"

        # Hours
        elif hours == 1:
            output = f"{hours} hr"
        else:
            output = f"{hours} hrs"

    # Days
    elif days == 1:
        output = f"{days} day"
    else:
        output = f"{days} days"

    return output


def initialize_version_control(filepath, filename):
    _paths = config.get_paths(filepath)

    _root = _paths[config.PATHS_KEYS.ROOT_FOLDER]
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]
    _saves = _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER]
    _objects = _paths[config.PATHS_KEYS.OBJECTS_FOLDER]
    _persisted_state = _paths[config.PATHS_KEYS.PERSISTED_STATE_FILE]

    # generate folder structure
    if not os.path.exists(_root):
        os.mkdir(_root)

    if not os.path.exists(_timelines):
        os.mkdir(_timelines)

    if not os.path.exists(_saves):
        os.mkdir(_saves)

    if not os.path.exists(_objects):
        os.mkdir(_objects)

    _original_tl_path = os.path.join(
        _timelines, config.PATHS_KEYS.ORIGINAL_TL_FILE)
    if not os.path.exists(_original_tl_path):
        # generate first checkpoint
        _initial_checkpoint_id = f"{uuid.uuid4().hex}.blend"

        source_file = os.path.join(filepath, filename)
        destination_file = os.path.join(_saves, _initial_checkpoint_id)
        shutil.copy(source_file, destination_file)

        datetimeString = datetime.now(timezone.utc).strftime(CP_TIME_FORMAT)

        with open(_original_tl_path, "w") as file:
            first_checkpoint = [{
                "id": _initial_checkpoint_id,
                "description": "Initial checkpoint",
                "date": datetimeString
            }]
            json.dump(first_checkpoint, file)

    if not os.path.exists(_persisted_state):
        # generate initial state
        with open(_persisted_state, "w") as file:
            initial_state = {
                "current_timeline": config.PATHS_KEYS.ORIGINAL_TL_FILE,
                "active_checkpoint": _initial_checkpoint_id,
                "disk_usage": 0,
                "filename": filename
            }
            json.dump(initial_state, file)


def get_checkpoints(filepath, timeline=config.PATHS_KEYS.ORIGINAL_TL_FILE):
    _paths = config.get_paths(filepath)

    timeline_path = os.path.join(
        _paths[config.PATHS_KEYS.TIMELINES_FOLDER], timeline)
    with open(timeline_path) as f:
        timeline_history = json.load(f)

        return timeline_history


def add_checkpoint(filepath, description):
    _paths = config.get_paths(filepath)
    _saves = _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER]
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]
    state = config.get_state(filepath)
    filename = state["filename"]
    current_timeline = state["current_timeline"]

    # new checkpoint ID
    checkpoint_id = f"{uuid.uuid4().hex}.blend"

    # Copy current file and pastes into saves
    source_file = os.path.join(filepath, filename)
    destination_file = os.path.join(_saves, checkpoint_id)
    shutil.copy(source_file, destination_file)

    # updates timeline info
    timeline_path = os.path.join(_timelines, current_timeline)
    with open(timeline_path, 'r+') as f:
        timeline_history = json.load(f)

        datetimeString = datetime.now(timezone.utc).strftime(CP_TIME_FORMAT)

        checkpoint = {
            "id": checkpoint_id,
            "description": description.strip(" \t\n\r"),
            "date": datetimeString
        }

        timeline_history.insert(0, checkpoint)

        f.seek(0)
        json.dump(timeline_history, f, indent=4)
        f.truncate()

    config.set_state(filepath, "active_checkpoint", checkpoint_id)
    config.set_state(filepath, "disk_usage", _get_disk_usage(
        os.path.join(filepath, config.PATHS_KEYS.ROOT_FOLDER)))


def load_checkpoint(filepath, checkpoint_id):
    _paths = config.get_paths(filepath)
    state = config.get_state(filepath)

    config.set_state(filepath, "active_checkpoint", checkpoint_id)

    checkpoint_path = os.path.join(
        _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER], checkpoint_id)
    filename = state["filename"]
    destination_file = os.path.join(filepath, filename)

    shutil.copy(checkpoint_path, destination_file)


def delete_checkpoint(filepath, checkpoint_index):
    _paths = config.get_paths(filepath)
    state = config.get_state(filepath)
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]
    _checkpoints = _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER]

    current_timeline = os.path.join(
        _timelines, state["current_timeline"])
    with open(current_timeline, "r+") as f:
        timeline_history = json.load(f)

        checkpoint_id = timeline_history[checkpoint_index]["id"]

        del timeline_history[checkpoint_index]

        f.seek(0)
        json.dump(timeline_history, f, indent=4)
        f.truncate()

    timelines = list(
        filter(lambda f: f != state["current_timeline"], os.listdir(_timelines)))

    shouldDelete = True

    if timelines:
        for tl in timelines:
            if not shouldDelete:
                break
            with open(os.path.join(_timelines, tl)) as f:
                checkpoints_data = json.load(f)
                for obj in checkpoints_data:
                    if obj["id"] == checkpoint_id:
                        shouldDelete = False
                        break

    if shouldDelete:
        os.remove(os.path.join(_checkpoints, checkpoint_id))
        config.set_state(filepath, "disk_usage", _get_disk_usage(
            os.path.join(filepath, config.PATHS_KEYS.ROOT_FOLDER)))


def edit_checkpoint(filepath, checkpoint_index, description):
    _paths = config.get_paths(filepath)
    state = config.get_state(filepath)

    current_timeline = os.path.join(
        _paths[config.PATHS_KEYS.TIMELINES_FOLDER], state["current_timeline"])
    with open(current_timeline, "r+") as f:
        timeline_history = json.load(f)

        timeline_history[checkpoint_index]["description"] = description

        f.seek(0)
        json.dump(timeline_history, f, indent=4)
        f.truncate()


def export_checkpoint(filepath, checkpoint_id, description):
    _paths = config.get_paths(filepath)

    # get checkpoint wth the provided id
    checkpoint = os.path.join(
        _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER], checkpoint_id)

    # create folder "exported"
    export_path = os.path.join(filepath, "exported")
    if not os.path.exists(export_path):
        os.mkdir(export_path)

    export_name = os.path.join(export_path, f"{description}.blend")
    shutil.copy(checkpoint, export_name)


def listall_timelines(filepath):
    _paths = config.get_paths(
        filepath)
    return os.listdir(_paths[config.PATHS_KEYS.TIMELINES_FOLDER])


def create_new_timeline(filepath, name, start_checkpoint_index, keep_history):
    state = config.get_state(filepath)
    _paths = config.get_paths(filepath)
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]

    new_name = f"{name}.json"
    new_tl_path = os.path.join(_timelines, new_name)

    if os.path.exists(new_tl_path):
        raise FileExistsError(f"File '{name}' already exists")

    # Get current timeline history
    # TODO test if "get_checkpoints" can be switched with cps_context.checkpoints
    current_timeline = state["current_timeline"]
    timeline_history = get_checkpoints(filepath, current_timeline)

    if keep_history:
        new_tl_history = timeline_history[start_checkpoint_index:]
    else:
        new_tl_history = [timeline_history[start_checkpoint_index]]

    # create new timeline file
    with open(new_tl_path, "w") as file:
        json.dump(new_tl_history, file)

    return new_name


def delete_timeline(filepath, name, checkpoints_count):
    _paths = config.get_paths(filepath)
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]

    # Set the iteration number to 1
    i = 0
    # Loop through the collection while the iteration number is less than or equal to the length of the collection
    while i < checkpoints_count:
        delete_checkpoint(filepath, 0)
        # Increment the iteration number
        i += 1

    delete_tl_path = os.path.join(_timelines, name)
    os.remove(delete_tl_path)


def rename_timeline(filepath, name):
    state = config.get_state(filepath)
    _paths = config.get_paths(filepath)
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]

    new_name = f"{name}.json"
    new_tl_path = os.path.join(_timelines, new_name)
    if os.path.exists(new_tl_path):
        raise FileExistsError(f"File '{name}' already exists")

    previous_tl_name = state["current_timeline"]
    previous_tl_path = os.path.join(_timelines, previous_tl_name)

    os.rename(previous_tl_path, new_tl_path)
    config.set_state(filepath, "current_timeline", new_name)


def switch_timeline(filepath, timeline=config.PATHS_KEYS.ORIGINAL_TL_FILE):
    _paths = config.get_paths(filepath)
    state = config.get_state(filepath)

    config.set_state(filepath, "current_timeline", timeline)

    timeline_path = os.path.join(
        _paths[config.PATHS_KEYS.TIMELINES_FOLDER], timeline)
    with open(timeline_path) as f:
        timeline_history = json.load(f)
        first_checkpoint = timeline_history[0]
        checkpoint = os.path.join(
            _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER], first_checkpoint["id"])

        config.set_state(filepath, "active_checkpoint", first_checkpoint["id"])

        filename = state["filename"]
        destination_file = os.path.join(filepath, filename)
        shutil.copy(checkpoint, destination_file)


def check_is_modified(filepath):
    state = config.get_state(filepath)
    _paths = config.get_paths(filepath)
    _saves = _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER]

    filename = state["filename"]
    active_checkpoint = state["active_checkpoint"]

    source_file = os.path.join(filepath, filename)
    active_checkpoint_file = os.path.join(_saves, active_checkpoint)

    stat1 = os.stat(source_file)
    stat2 = os.stat(active_checkpoint_file)
    return stat1.st_size != stat2.st_size
