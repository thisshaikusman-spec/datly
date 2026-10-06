from typing import BinaryIO

import pandas as pd


def load_csv(file: BinaryIO) -> pd.DataFrame:
    return pd.read_csv(file)
