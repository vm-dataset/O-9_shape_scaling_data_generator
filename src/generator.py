"""Chess generator example - REPLACE THIS WITH YOUR TASK."""

import random
from PIL import Image, ImageDraw
from core import BaseGenerator, TaskPair, TaskMetadata, ImageRenderer
from .prompts import CHESS_PROMPTS


class ChessGenerator(BaseGenerator):
    """Example chess generator. Replace with your own task logic."""
    
    def __init__(self, config):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)
        
        # Simple templates (in real impl, generate algorithmically)
        self.templates = [
            {"pieces": [("K", "g1"), ("R", "a1"), ("k", "h8"), ("p", "h7")], "solution": "Ra8#"},
            {"pieces": [("K", "g6"), ("Q", "e5"), ("k", "h8")], "solution": "Qg7#"},
            {"pieces": [("K", "f6"), ("R", "a1"), ("k", "h8")], "solution": "Rh1#"},
        ]
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one chess task."""
        template = random.choice(self.templates)
        
        # Render board
        first_image = self._render_board(template["pieces"])
        final_image = self._render_board_with_mate(template["pieces"])
        
        # Select prompt
        prompt = random.choice(CHESS_PROMPTS)
        
        # Create metadata
        metadata = TaskMetadata(
            id=task_id,
            domain=self.config.domain,
            difficulty="easy",
            tags=["chess", "mate_in_one"],
            metadata={"solution": template["solution"]}
        )
        
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            metadata=metadata
        )
    
    def _render_board(self, pieces: list) -> Image.Image:
        """Render chess board (simplified)."""
        img = self.renderer.create_blank_image()
        img = self.renderer.draw_grid(img, 8, 8)
        
        # Draw pieces as text (simplified)
        square_size = self.config.image_size[0] // 8
        for piece, square in pieces:
            col, row = ord(square[0]) - ord('a'), 8 - int(square[1])
            x = col * square_size + square_size // 3
            y = row * square_size + square_size // 3
            
            symbols = {'K': '♔', 'Q': '♕', 'R': '♖', 'k': '♚', 'q': '♛', 'r': '♜', 'p': '♟'}
            self.renderer.draw_text(img, symbols.get(piece, piece), (x, y))
        
        return img
    
    def _render_board_with_mate(self, pieces: list) -> Image.Image:
        """Render board with checkmate indicator."""
        img = self._render_board(pieces)
        self.renderer.draw_text(img, "Checkmate!", (150, 10))
        return img
