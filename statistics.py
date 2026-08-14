from dataclasses import dataclass

@dataclass
class ConversionStat:

    filename: str

    input_type: str

    output_type: str

    rows: int

    columns: int

    input_size: float

    output_size: float

    elapsed: float

    status: str