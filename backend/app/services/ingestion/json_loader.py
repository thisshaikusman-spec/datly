from typing import BinaryIO

import pandas as pd


def load_json(file: BinaryIO) -> pd.DataFrame:
    return pd.read_json(file)
