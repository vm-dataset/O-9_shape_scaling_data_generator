"""Task configuration - CUSTOMIZE FOR YOUR TASK."""

from pydantic import BaseModel, Field


class ChessConfig(BaseModel):
    """Chess-specific config. Replace with your task config."""
    board_size: int = Field(default=400)
    piece_style: str = Field(default="standard")


# Example for your task:
# class YourTaskConfig(BaseModel):
#     grid_size: int = Field(default=10)
#     difficulty_level: str = Field(default="medium")
