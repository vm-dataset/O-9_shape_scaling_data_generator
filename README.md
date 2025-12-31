# Template Data Generator 🎲

A minimal template for creating synthetic reasoning task generators. Fork this and customize it for your own task (maze, sudoku, rotation, etc.).

---

## 🚀 Quick Start

```bash
# 1. Use this template on GitHub (click "Use this template")

# 2. Clone your new repo
git clone https://github.com/your-org/your-task-generator.git
cd your-task-generator

# 3. Install
pip install -r requirements.txt
pip install -e .

# 4. Generate example tasks
python examples/generate.py --num-samples 10
```

---

## 📁 Structure

```
template-data-generator/
├── core/                    # ✅ KEEP: Standard utilities
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   └── output_writer.py    # File output
├── src/                     # ⚠️ CUSTOMIZE: Your task logic
│   ├── generator.py        # Replace ChessGenerator with yours
│   ├── prompts.py          # Your prompt templates
│   └── config.py           # Your configuration
├── examples/
│   └── generate.py         # Example usage
└── data/questions/         # Generated output
```

---

## 📦 Output Format

Every generator produces:

```
data/questions/{task}_task/{task_id}/
├── first_frame.png          # Initial state (REQUIRED)
├── final_frame.png          # Goal state (or goal.txt)
├── prompt.txt               # Instructions (REQUIRED)
└── question_metadata.json   # Metadata (REQUIRED)
```

---

## 🎨 Customization (3 Steps)

### 1. Update `src/generator.py`

Replace `ChessGenerator` with your task:

```python
from core import BaseGenerator, TaskPair, TaskMetadata, ImageRenderer

class MazeGenerator(BaseGenerator):
    def __init__(self, config):
        super().__init__(config)
        self.renderer = ImageRenderer(config.image_size)
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        # 1. Generate your problem
        maze = self.create_maze()
        
        # 2. Solve it
        solution = self.solve_maze(maze)
        
        # 3. Render images
        first_image = self.render_maze(maze)
        final_image = self.render_maze_with_solution(maze, solution)
        
        # 4. Create TaskPair
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=self.select_prompt(),
            first_image=first_image,
            final_image=final_image,
            metadata=TaskMetadata(
                id=task_id,
                domain=self.config.domain,
                difficulty="medium",
                tags=["maze", "pathfinding"]
            )
        )
```

### 2. Update `src/prompts.py`

Replace chess prompts with yours:

```python
MAZE_PROMPTS = [
    "Animate a path from start to goal through the maze.",
    "Show the solution route navigating through corridors.",
]
```

### 3. Update `src/config.py` (optional)

Add task-specific settings:

```python
class MazeConfig(BaseModel):
    grid_size: int = Field(default=10)
    wall_thickness: int = Field(default=2)
```

---

## 🖼️ Using ImageRenderer

```python
from core import ImageRenderer

renderer = ImageRenderer(image_size=(400, 400))

# Create blank canvas
img = renderer.create_blank_image()

# Draw grid
img = renderer.draw_grid(img, rows=10, cols=10)

# Draw text
img = renderer.draw_text(img, "Hello", (50, 50))

# Ensure RGB mode
img = ImageRenderer.ensure_rgb(img)
```

---

## 💡 Usage Examples

### Basic Generation

```bash
python examples/generate.py --num-samples 50
```

### With Seed (Reproducible)

```bash
python examples/generate.py --num-samples 100 --seed 42
```

### Python API

```python
from core import GenerationConfig, OutputWriter
from src import ChessGenerator

config = GenerationConfig(
    num_samples=50,
    domain="chess",
    random_seed=42
)

generator = ChessGenerator(config)
tasks = generator.generate_dataset()

writer = OutputWriter(config.output_dir)
writer.write_dataset(tasks)
```

---

## 📋 Output Specification

### Required Files

**first_frame.png**
- PNG format, RGB mode
- 400x400 pixels (or configured size)
- Shows initial problem state

**final_frame.png** (or goal.txt for text answers)
- PNG format, RGB mode, same size as first_frame
- Shows solution/goal state
- Use `goal.txt` for text-based answers

**prompt.txt**
- Plain text, UTF-8
- 50-200 words recommended
- Instructions for video generation

**question_metadata.json**
```json
{
  "id": "chess_0001",
  "domain": "chess",
  "prompt": "Animate the chess...",
  "difficulty": "easy",
  "tags": ["chess", "mate_in_one"],
  "created_at": "2025-01-01T00:00:00Z",
  "metadata": {
    "solution": "Qg7#"
  }
}
```

Required fields: `id`, `domain`, `prompt`, `difficulty`, `created_at`

Optional fields: `tags`, `metadata` (any extra task data)

---

## 🔧 Core Components

### BaseGenerator

```python
class BaseGenerator(ABC):
    @abstractmethod
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Implement this method."""
        pass
    
    def generate_dataset(self) -> List[TaskPair]:
        """Generates full dataset."""
        pass
```

### TaskPair

```python
TaskPair(
    task_id="maze_0001",
    domain="maze",
    prompt="Navigate through the maze...",
    first_image=PIL.Image,
    final_image=PIL.Image,
    metadata=TaskMetadata(...)
)
```

### OutputWriter

```python
writer = OutputWriter("data/questions")
writer.write_task_pair(task_pair)
writer.write_dataset(task_pairs)
```

---

## 📚 Key Classes

| Class | Purpose | Location |
|-------|---------|----------|
| `BaseGenerator` | Abstract generator | `core/base_generator.py` |
| `GenerationConfig` | Generation settings | `core/base_generator.py` |
| `TaskPair` | Task data structure | `core/schemas.py` |
| `TaskMetadata` | Task metadata | `core/schemas.py` |
| `ImageRenderer` | Image utilities | `core/image_utils.py` |
| `OutputWriter` | File output | `core/output_writer.py` |

---

## 🔄 Workflow

1. **Implement** `generate_task_pair()` in your generator
2. **Configure** with `GenerationConfig`
3. **Generate** dataset with `generate_dataset()`
4. **Write** to disk with `OutputWriter`
5. **Use** with video reasoning frameworks (VMEvalKit, etc.)

---

## 📝 Prompt Writing Tips

Good prompts:
- Describe the action/animation clearly
- Mention initial and final states
- Use action verbs (animate, show, demonstrate)
- Be specific but concise (50-150 words)

Example:
```
"Animate a path from the green start to the red goal. 
The path should navigate through maze corridors without 
crossing walls, showing the solution step by step."
```

---

## ⚙️ Dependencies

Minimal requirements:
- `numpy` - Array operations
- `Pillow` - Image processing
- `pydantic` - Data validation

Add task-specific deps to `requirements.txt`.

---

## 📄 License

MIT License - fork freely!

---

## 🔗 Related

- **template-data-pipeline** - For benchmark datasets
- **VMEvalKit** - Video reasoning evaluation
- **Your task generator** - Share with community!

---

## 💬 Questions?

This is a template repository. Fork it and make it yours! 🚀
