"""Output writer for standard format."""

import json
from pathlib import Path
from typing import List
from .schemas import TaskPair
from .image_utils import ImageRenderer


class OutputWriter:
    """Writes tasks to standard folder structure."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write_task_pair(self, task_pair: TaskPair) -> Path:
        """Write single task to disk."""
        # Create directory
        task_dir = self.output_dir / f"{task_pair.domain}_task" / task_pair.task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Write images
        first_img = ImageRenderer.ensure_rgb(task_pair.first_image)
        first_img.save(task_dir / "first_frame.png", "PNG")
        
        if task_pair.final_image:
            final_img = ImageRenderer.ensure_rgb(task_pair.final_image)
            final_img.save(task_dir / "final_frame.png", "PNG")
        elif task_pair.goal_text:
            (task_dir / "goal.txt").write_text(task_pair.goal_text)
        
        # Write prompt
        (task_dir / "prompt.txt").write_text(task_pair.prompt)
        
        # Write metadata
        metadata = {
            "id": task_pair.task_id,
            "domain": task_pair.domain,
            "prompt": task_pair.prompt,
            "difficulty": task_pair.metadata.difficulty,
            "tags": task_pair.metadata.tags,
            "created_at": task_pair.metadata.created_at,
            "metadata": task_pair.metadata.metadata
        }
        
        with open(task_dir / "question_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return task_dir
    
    def write_dataset(self, task_pairs: List[TaskPair]) -> Path:
        """Write all tasks to disk."""
        print(f"\n📁 Writing {len(task_pairs)} tasks to {self.output_dir}")
        for pair in task_pairs:
            self.write_task_pair(pair)
        print(f"✅ Complete!\n")
        return self.output_dir
