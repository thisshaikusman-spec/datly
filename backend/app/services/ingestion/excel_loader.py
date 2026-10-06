from typing import BinaryIO

import pandas as pd


def load_excel(file: BinaryIO) -> pd.DataFrame:
    return pd.read_excel(file)
