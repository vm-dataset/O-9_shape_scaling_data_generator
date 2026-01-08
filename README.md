# Shape Scaling Data Generator 📏

A specialized data generator for creating synthetic **shape scaling transformation** tasks in the format A:B :: C:?. Perfect for training models on visual reasoning and analogical thinking with size transformations.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/shape-scaling-data-generator.git
cd shape-scaling-data-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate tasks
python examples/generate.py --num-samples 50
```

---

## 📁 Structure

```
shape-scaling-data-generator/
├── core/                    # Framework utilities
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # Shape scaling implementation
│   ├── generator.py        # Shape scaling generator
│   ├── prompts.py          # Scaling prompts
│   └── config.py           # Scaling configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── shape_scaling_task/ # Scaling task outputs
```

---

## 📦 Output Format

Every generator produces:

```
data/questions/shape_scaling_task/{task_id}/
├── first_frame.png          # Shows A→B :: C→? layout
├── final_frame.png          # Shows A→B :: C→D (answer)
├── prompt.txt               # Scaling transformation instruction
└── ground_truth.mp4         # Smooth scaling animation
```

---

## 🎯 Current Implementation: Scaling Transformations

The current implementation generates **visual analogy tasks** in the format **A:B :: C:?** focused on **size scaling**.

### **Task Type:**
- **Scaling**: Size transformations (small → large, large → small)

### **Supported Shapes:**
- **Basic Shapes**: Square, Triangle, Circle, Diamond, Pentagon, Hexagon
- **Extended Shapes**: Rectangle, Oval, Star, Heart
- All shapes support scaling up (1.3x, 1.4x, 1.5x, 1.7x) and scaling down (0.5x, 0.6x, 0.7x, 0.8x)

### **Example Tasks:**
1. **Scale Down**: `large_square → small_square :: large_triangle → small_triangle`
2. **Scale Up**: `small_circle → large_circle :: small_star → large_star`
3. **Mixed Shapes**: `large_pentagon → small_pentagon :: large_heart → small_heart`

### **Features:**
- **Diverse Shapes**: 10 different shape types for variety
- **Balanced Scaling**: Both scaling up and scaling down transformations
- **Smooth Animation**: Videos show gradual size transformation
- **Clear Visual Layout**: A → B :: C → ? format with arrows

---

## 🎨 Customization

This generator is specifically designed for shape scaling tasks. Key customizable parameters:

### Configuration (`src/config.py`)
- **Shapes**: 10 different shape types (square, triangle, circle, etc.)
- **Scaling Factors**: Both up-scaling (1.3x-1.7x) and down-scaling (0.5x-0.8x)
- **Image Size**: Default 512x512 with configurable margins
- **Video Settings**: Frame rate, animation duration

### Prompts (`src/prompts.py`)
- Scaling-specific instructions
- Multiple prompt variations for diversity

### Shape Rendering (`src/generator.py`)
- Clean shape drawing without artifacts
- Automatic bounds checking
- Smooth scaling animations

**Single entry point:** `python examples/generate.py --num-samples 50`