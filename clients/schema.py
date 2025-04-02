from typing_extensions import Annotated
from pydantic import BaseModel, Field
from typing import List


SerializedBase64 = Annotated[bytes, Field(json_schema_extra={"format": "base64"})]


class FileType(BaseModel):
    """
    Represents a gsa file.

    Attributes:
        filename (str): The name of the file.
        file (SerializedBase64): The file content serialized in Base64 format.
    """

    filename: str
    file: SerializedBase64


class TransitionData(BaseModel):
    """
    Represents a transition data record.

    Attributes:
        id (str): The campaign id for the transition data record.
        temp (float): The temperature value associated with the transition.
        ylist (List[float]): A list of float values representing the observed peaks (d-Spacing) associated with temp.
    """

    id: str
    temp: float
    ylist: List[float]


class NextTemperature(BaseModel):
    """
    Represents the next temperature record (ANDiE prediction).

    Attributes:
        id (str): The campaign id for the next temperature data record.
        data (float): The predicted temperature value.
        timestamp (int): The timestamp when the prediction was recorded.
    """

    id: str
    data: float
    timestamp: int
