
from pathlib import Path
import json


class Saves:

    def __init__(self):
        self.file_path = Path(Path(__file__).parent, 'saves.json')

        self.data = {}

        self._load()

    def _load(self):
        """
        Loads dict from json
        :return:
        """
        if self.file_path.exists():
            with open(self.file_path) as fid:
                self.data = json.load(fid)

    def _save(self):
        """
        Writes information to json file.
        :return:
        """
        with open(self.file_path, 'w') as fid:
            json.dump(self.data, fid, indent=4, sort_keys=True)

    def set(self, key, value):
        self.data[key] = value
        self._save()

    def get(self, key, default=''):
        return self.data.get(key, default)


class SaveSelection:
    _saves = Saves()
    _saves_id_key = ''
    _selections_to_store = []

    def save_selection(self):
        data = {}
        for comp in self._selections_to_store:
            try:
                data[comp] = getattr(self, comp).get()
            except:
                pass
        self._saves.set(self._saves_id_key, data)

    def load_selection(self):
        data = self._saves.get(self._saves_id_key)
        for comp in self._selections_to_store:
            try:
                item = data.get(comp, None)
                if item is None:
                    continue
                getattr(self, comp).set(item)
            except:
                pass

