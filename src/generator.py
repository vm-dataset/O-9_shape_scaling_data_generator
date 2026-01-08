"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           SHAPE MATCHING TASK GENERATOR                       ║
║                                                                               ║
║  Generates analog shape matching tasks (A:B :: C:?)                           ║
║  Example: square → rounded square, triangle → rounded triangle                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import tempfile
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple, Any

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


class TaskGenerator(BaseGenerator):
    """
    Shape matching task generator.
    
    Creates visual analogies in the format A:B :: C:?
    where shapes undergo transformations like rounding, scaling, rotation, etc.
    """
    
    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)
        
        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")
        
        # Shape definitions - expanded set for more variety
        self.base_shapes = [
            "square", "triangle", "circle", "diamond", "pentagon", "hexagon",
            "rectangle", "oval", "star", "heart", "cross", "arrow", "trapezoid",
            "rhombus", "octagon", "crescent", "plus", "minus", "L_shape", "T_shape"
        ]
        
        # Single color for all shapes (since we're only doing scaling)
        self.shape_color = (70, 130, 180)  # Blue
        
        # Scaling factors - expanded set with more granular scaling options
        self.scale_factors = [
            0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95,  # Shrinking
            1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5, 1.55, 1.6, 1.65, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2.0, 2.1, 2.2  # Growing
        ]
        
        # Track generated combinations to prevent duplicates
        self.generated_combinations = set()
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one shape matching task pair."""
        
        # Generate task data
        task_data = self._generate_task_data()
        
        # Render images
        first_image = self._render_initial_state(task_data)
        final_image = self._render_final_state(task_data)
        
        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, task_data)
        
        # Select prompt
        prompt = get_prompt(task_data.get("transformation_type", "default"))
        
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )
    
    # ══════════════════════════════════════════════════════════════════════════
    #  TASK DATA GENERATION
    # ══════════════════════════════════════════════════════════════════════════
    
    def _generate_task_data(self) -> Dict[str, Any]:
        """Generate scaling transformation task data with duplicate prevention."""
        
        # Calculate total possible unique combinations
        num_shapes = len(self.base_shapes)
        num_scale_factors = len(self.scale_factors)
        max_unique_combinations = num_shapes * (num_shapes - 1) * num_scale_factors
        
        # If we haven't exhausted all combinations, ensure uniqueness
        if len(self.generated_combinations) < max_unique_combinations:
            max_attempts = 1000  # Increase attempts for better coverage
            for attempt in range(max_attempts):
                # Select two different shapes for the analogy
                shape_a, shape_c = random.sample(self.base_shapes, 2)
                scale_factor = random.choice(self.scale_factors)
                
                # Create a unique identifier for this combination
                combination_key = (shape_a, shape_c, scale_factor)
                
                # Check if this combination has been used before
                if combination_key not in self.generated_combinations:
                    self.generated_combinations.add(combination_key)
                    return self._generate_scaling_task(shape_a, shape_c, scale_factor)
            
            # If we still can't find a unique combination after many attempts,
            # generate all remaining combinations systematically
            return self._generate_systematic_unique_combination()
        
        # If we've exhausted unique combinations, allow duplicates but warn
        if len(self.generated_combinations) == max_unique_combinations:
            print(f"⚠️  Warning: Generated all {max_unique_combinations} unique combinations. Allowing duplicates for remaining tasks.")
        
        shape_a, shape_c = random.sample(self.base_shapes, 2)
        scale_factor = random.choice(self.scale_factors)
        return self._generate_scaling_task(shape_a, shape_c, scale_factor)
    
    def _generate_systematic_unique_combination(self) -> Dict[str, Any]:
        """Generate a unique combination systematically when random selection fails."""
        # Generate all possible combinations and find one not yet used
        for shape_a in self.base_shapes:
            for shape_c in self.base_shapes:
                if shape_a == shape_c:
                    continue
                for scale_factor in self.scale_factors:
                    combination_key = (shape_a, shape_c, scale_factor)
                    if combination_key not in self.generated_combinations:
                        self.generated_combinations.add(combination_key)
                        return self._generate_scaling_task(shape_a, shape_c, scale_factor)
        
        # This should never happen if our math is correct
        raise RuntimeError("Failed to generate unique combination - this should not happen!")
    
    def _generate_scaling_task(self, shape_a: str, shape_c: str, scale_factor: float) -> Dict[str, Any]:
        """Generate a scaling transformation task."""
        scale_description = "smaller" if scale_factor < 1.0 else "larger"
        
        return {
            "transformation_type": "scaling",
            "shape_a": shape_a,
            "shape_b": shape_a,  # Same shape, different size
            "shape_c": shape_c,
            "shape_d": shape_c,  # Same shape, different size
            "scale_factor": scale_factor,
            "description": f"{shape_a} becomes {scale_description} {shape_a}, {shape_c} becomes {scale_description} {shape_c}"
        }
    
    # ══════════════════════════════════════════════════════════════════════════
    #  IMAGE RENDERING
    # ══════════════════════════════════════════════════════════════════════════
    
    def _render_initial_state(self, task_data: Dict[str, Any]) -> Image.Image:
        """Render the initial state with A:B :: C:? layout."""
        img = self.renderer.create_blank_image()
        draw = ImageDraw.Draw(img)
        
        width, height = self.config.image_size
        margin = self.config.margin
        shape_size = self.config.shape_size
        
        # Layout positions
        # A    →    B
        # C    →    ?
        
        positions = {
            "A": (margin + shape_size//2, height//4),
            "arrow1": (width//2, height//4),
            "B": (width - margin - shape_size//2, height//4),
            "C": (margin + shape_size//2, 3*height//4),
            "arrow2": (width//2, 3*height//4),
            "question": (width - margin - shape_size//2, 3*height//4)
        }
        
        # Draw shapes and arrows
        self._draw_shape_at_position(draw, task_data["shape_a"], positions["A"], shape_size, task_data)
        self._draw_arrow(draw, positions["arrow1"])
        self._draw_transformed_shape_at_position(draw, task_data["shape_b"], positions["B"], shape_size, task_data, "B")
        
        self._draw_shape_at_position(draw, task_data["shape_c"], positions["C"], shape_size, task_data)
        self._draw_arrow(draw, positions["arrow2"])
        self._draw_question_mark(draw, positions["question"])
        
        return img
    
    def _render_final_state(self, task_data: Dict[str, Any]) -> Image.Image:
        """Render the final state with the answer revealed."""
        img = self.renderer.create_blank_image()
        draw = ImageDraw.Draw(img)
        
        width, height = self.config.image_size
        margin = self.config.margin
        shape_size = self.config.shape_size
        
        # Same layout as initial state
        positions = {
            "A": (margin + shape_size//2, height//4),
            "arrow1": (width//2, height//4),
            "B": (width - margin - shape_size//2, height//4),
            "C": (margin + shape_size//2, 3*height//4),
            "arrow2": (width//2, 3*height//4),
            "D": (width - margin - shape_size//2, 3*height//4)
        }
        
        # Draw shapes and arrows
        self._draw_shape_at_position(draw, task_data["shape_a"], positions["A"], shape_size, task_data)
        self._draw_arrow(draw, positions["arrow1"])
        self._draw_transformed_shape_at_position(draw, task_data["shape_b"], positions["B"], shape_size, task_data, "B")
        
        self._draw_shape_at_position(draw, task_data["shape_c"], positions["C"], shape_size, task_data)
        self._draw_arrow(draw, positions["arrow2"])
        self._draw_transformed_shape_at_position(draw, task_data["shape_d"], positions["D"], shape_size, task_data, "D")
        
        return img
    
    def _draw_shape_at_position(self, draw: ImageDraw.Draw, shape: str, position: Tuple[int, int], size: int, task_data: Dict[str, Any]):
        """Draw a shape at the specified position."""
        x, y = position
        color = self.shape_color
        
        if shape.startswith("rounded_"):
            base_shape = shape.replace("rounded_", "")
            self._draw_rounded_shape(draw, base_shape, x, y, size, color)
        else:
            self._draw_base_shape(draw, shape, x, y, size, color)
    
    def _draw_transformed_shape_at_position(self, draw: ImageDraw.Draw, shape: str, position: Tuple[int, int], size: int, task_data: Dict[str, Any], shape_label: str):
        """Draw a transformed shape at the specified position."""
        x, y = position
        color = self.shape_color
        
        # Apply scaling transformation with bounds checking
        if task_data["transformation_type"] == "scaling" and shape_label in ["B", "D"]:
            scaled_size = int(size * task_data["scale_factor"])
            # Ensure the scaled shape fits within bounds with margin
            max_allowed_size = self._get_max_shape_size_for_position(x, y)
            size = min(scaled_size, max_allowed_size)
        
        self._draw_base_shape(draw, shape, x, y, size, color)
    
    def _get_max_shape_size_for_position(self, x: int, y: int) -> int:
        """Calculate maximum shape size that fits at given position with margin."""
        width, height = self.config.image_size
        margin = self.config.margin
        
        # Calculate available space from position to edges
        space_left = x - margin
        space_right = width - x - margin
        space_top = y - margin
        space_bottom = height - y - margin
        
        # Maximum radius (half-size) is the minimum of available spaces
        max_radius = min(space_left, space_right, space_top, space_bottom)
        
        # Add some extra margin for safety (especially for complex shapes like stars)
        safety_margin = 10
        max_radius = max(max_radius - safety_margin, 20)  # Minimum size of 20
        
        return max_radius * 2  # Return diameter (full size)
    
    def _draw_base_shape(self, draw: ImageDraw.Draw, shape: str, x: int, y: int, size: int, color: Tuple[int, int, int]):
        """Draw a basic geometric shape."""
        half_size = size // 2
        
        if shape == "square":
            draw.rectangle([x-half_size, y-half_size, x+half_size, y+half_size], fill=color, outline=(0,0,0), width=2)
        
        elif shape == "circle":
            draw.ellipse([x-half_size, y-half_size, x+half_size, y+half_size], fill=color, outline=(0,0,0), width=2)
        
        elif shape == "triangle":
            points = [
                (x, y-half_size),  # top
                (x-half_size, y+half_size),  # bottom left
                (x+half_size, y+half_size)   # bottom right
            ]
            draw.polygon(points, fill=color, outline=(0,0,0), width=2)
        
        elif shape == "diamond":
            points = [
                (x, y-half_size),  # top
                (x+half_size, y),  # right
                (x, y+half_size),  # bottom
                (x-half_size, y)   # left
            ]
            draw.polygon(points, fill=color, outline=(0,0,0), width=2)
        
        elif shape == "pentagon":
            points = []
            for i in range(5):
                angle = i * 2 * math.pi / 5 - math.pi/2  # Start from top
                px = x + half_size * math.cos(angle)
                py = y + half_size * math.sin(angle)
                points.append((px, py))
            draw.polygon(points, fill=color, outline=(0,0,0), width=2)
        
        elif shape == "hexagon":
            points = []
            for i in range(6):
                angle = i * 2 * math.pi / 6
                px = x + half_size * math.cos(angle)
                py = y + half_size * math.sin(angle)
                points.append((px, py))
            draw.polygon(points, fill=color, outline=(0,0,0), width=2)
        
        elif shape == "rectangle":
            # Rectangle (wider than tall)
            width_factor = 1.4
            rect_width = int(half_size * width_factor)
            rect_height = int(half_size * 0.7)
            draw.rectangle([x-rect_width, y-rect_height, x+rect_width, y+rect_height], fill=color, outline=(0,0,0), width=2)
        
        elif shape == "oval":
            # Oval (wider than tall)
            width_factor = 1.4
            oval_width = int(half_size * width_factor)
            oval_height = int(half_size * 0.7)
            draw.ellipse([x-oval_width, y-oval_height, x+oval_width, y+oval_height], fill=color, outline=(0,0,0), width=2)
        
        elif shape == "star":
            # 5-pointed star - draw as separate triangular segments to avoid extra lines
            outer_radius = half_size
            inner_radius = half_size * 0.4
            
            # Draw the star as 5 separate triangular segments
            for i in range(5):
                # Calculate angles for this star point
                outer_angle = i * 2 * math.pi / 5 - math.pi/2  # Outer point
                inner_angle1 = (i * 2 + 1) * math.pi / 5 - math.pi/2  # Left inner point
                inner_angle2 = (i * 2 - 1) * math.pi / 5 - math.pi/2  # Right inner point
                
                # Calculate coordinates
                outer_x = x + outer_radius * math.cos(outer_angle)
                outer_y = y + outer_radius * math.sin(outer_angle)
                inner_x1 = x + inner_radius * math.cos(inner_angle1)
                inner_y1 = y + inner_radius * math.sin(inner_angle1)
                inner_x2 = x + inner_radius * math.cos(inner_angle2)
                inner_y2 = y + inner_radius * math.sin(inner_angle2)
                
                # Draw triangle for this star point
                triangle_points = [(outer_x, outer_y), (inner_x1, inner_y1), (inner_x2, inner_y2)]
                draw.polygon(triangle_points, fill=color, outline=(0,0,0), width=2)
        
        elif shape == "heart":
            # Simple heart shape using circles and triangle
            # Two circles for the top
            circle_radius = int(half_size * 0.4)
            left_center_x = x - int(half_size * 0.3)
            right_center_x = x + int(half_size * 0.3)
            circle_center_y = y - int(half_size * 0.2)
            
            # Draw the two top circles
            draw.ellipse([left_center_x-circle_radius, circle_center_y-circle_radius,
                         left_center_x+circle_radius, circle_center_y+circle_radius], fill=color, outline=color)
            draw.ellipse([right_center_x-circle_radius, circle_center_y-circle_radius,
                         right_center_x+circle_radius, circle_center_y+circle_radius], fill=color, outline=color)
            
            # Triangle for the bottom part
            triangle_points = [
                (x, y + half_size),  # bottom point
                (left_center_x - circle_radius//2, circle_center_y),  # left
                (right_center_x + circle_radius//2, circle_center_y)   # right
            ]
            draw.polygon(triangle_points, fill=color, outline=color)
            
            # Draw outline
            draw.ellipse([left_center_x-circle_radius, circle_center_y-circle_radius,
                         left_center_x+circle_radius, circle_center_y+circle_radius], outline=(0,0,0), width=2)
            draw.ellipse([right_center_x-circle_radius, circle_center_y-circle_radius,
                         right_center_x+circle_radius, circle_center_y+circle_radius], outline=(0,0,0), width=2)
            draw.polygon(triangle_points, outline=(0,0,0), width=2)
        
        elif shape == "cross":
            # Cross shape
            thickness = half_size // 4
            # Vertical bar
            draw.rectangle([x-thickness, y-half_size, x+thickness, y+half_size], fill=color, outline=(0,0,0), width=2)
            # Horizontal bar
            draw.rectangle([x-half_size, y-thickness, x+half_size, y+thickness], fill=color, outline=(0,0,0), width=2)
        
        elif shape == "arrow":
            # Arrow pointing right
            points = [
                (x-half_size, y-half_size//2),  # left top
                (x, y-half_size//2),            # middle top
                (x, y-half_size),               # tip top
                (x+half_size, y),               # tip point
                (x, y+half_size),               # tip bottom
                (x, y+half_size//2),            # middle bottom
                (x-half_size, y+half_size//2)   # left bottom
            ]
            draw.polygon(points, fill=color, outline=(0,0,0), width=2)
        
        elif shape == "trapezoid":
            # Trapezoid (wider at bottom)
            top_width = half_size // 2
            points = [
                (x-top_width, y-half_size),     # top left
                (x+top_width, y-half_size),     # top right
                (x+half_size, y+half_size),     # bottom right
                (x-half_size, y+half_size)      # bottom left
            ]
            draw.polygon(points, fill=color, outline=(0,0,0), width=2)
        
        elif shape == "rhombus":
            # Rhombus (diamond rotated)
            points = [
                (x, y-half_size),               # top
                (x+half_size*0.7, y),           # right
                (x, y+half_size),               # bottom
                (x-half_size*0.7, y)            # left
            ]
            draw.polygon(points, fill=color, outline=(0,0,0), width=2)
        
        elif shape == "octagon":
            # Regular octagon
            points = []
            for i in range(8):
                angle = i * 2 * math.pi / 8
                px = x + half_size * math.cos(angle)
                py = y + half_size * math.sin(angle)
                points.append((px, py))
            draw.polygon(points, fill=color, outline=(0,0,0), width=2)
        
        elif shape == "crescent":
            # Crescent moon shape (two overlapping circles)
            # Draw larger circle
            draw.ellipse([x-half_size, y-half_size, x+half_size, y+half_size], fill=color, outline=(0,0,0), width=2)
            # Draw smaller circle to create crescent (using background color)
            offset = half_size // 3
            smaller_radius = int(half_size * 0.7)
            draw.ellipse([x-smaller_radius+offset, y-smaller_radius, x+smaller_radius+offset, y+smaller_radius],
                        fill=(255,255,255), outline=(0,0,0), width=2)
        
        elif shape == "plus":
            # Plus sign (thicker cross)
            thickness = half_size // 3
            # Vertical bar
            draw.rectangle([x-thickness, y-half_size, x+thickness, y+half_size], fill=color, outline=(0,0,0), width=2)
            # Horizontal bar
            draw.rectangle([x-half_size, y-thickness, x+half_size, y+thickness], fill=color, outline=(0,0,0), width=2)
        
        elif shape == "minus":
            # Minus sign (horizontal bar)
            thickness = half_size // 4
            draw.rectangle([x-half_size, y-thickness, x+half_size, y+thickness], fill=color, outline=(0,0,0), width=2)
        
        elif shape == "L_shape":
            # L shape
            thickness = half_size // 3
            # Vertical part
            draw.rectangle([x-half_size, y-half_size, x-half_size+thickness, y+half_size], fill=color, outline=(0,0,0), width=2)
            # Horizontal part
            draw.rectangle([x-half_size, y+half_size-thickness, x+half_size, y+half_size], fill=color, outline=(0,0,0), width=2)
        
        elif shape == "T_shape":
            # T shape
            thickness = half_size // 3
            # Horizontal top part
            draw.rectangle([x-half_size, y-half_size, x+half_size, y-half_size+thickness], fill=color, outline=(0,0,0), width=2)
            # Vertical part
            draw.rectangle([x-thickness//2, y-half_size, x+thickness//2, y+half_size], fill=color, outline=(0,0,0), width=2)
    
    def _draw_rounded_shape(self, draw: ImageDraw.Draw, shape: str, x: int, y: int, size: int, color: Tuple[int, int, int]):
        """Draw a rounded version of a shape."""
        half_size = size // 2
        corner_radius = size // 8
        
        if shape == "square":
            # Rounded rectangle
            self._draw_rounded_rectangle(draw, x-half_size, y-half_size, x+half_size, y+half_size, corner_radius, color)
        
        elif shape == "triangle":
            # Rounded triangle (approximate with smaller circles at vertices)
            points = [
                (x, y-half_size),  # top
                (x-half_size, y+half_size),  # bottom left
                (x+half_size, y+half_size)   # bottom right
            ]
            # Draw main triangle
            draw.polygon(points, fill=color, outline=color)
            # Add small circles at corners for rounding effect
            r = corner_radius
            for px, py in points:
                draw.ellipse([px-r, py-r, px+r, py+r], fill=color, outline=color)
        
        else:
            # For other shapes, just draw the base shape (could be enhanced)
            self._draw_base_shape(draw, shape, x, y, size, color)
    
    def _draw_rounded_rectangle(self, draw: ImageDraw.Draw, x1: int, y1: int, x2: int, y2: int, radius: int, color: Tuple[int, int, int]):
        """Draw a rounded rectangle."""
        # Main rectangle
        draw.rectangle([x1+radius, y1, x2-radius, y2], fill=color)
        draw.rectangle([x1, y1+radius, x2, y2-radius], fill=color)
        
        # Corner circles
        draw.ellipse([x1, y1, x1+2*radius, y1+2*radius], fill=color)  # top-left
        draw.ellipse([x2-2*radius, y1, x2, y1+2*radius], fill=color)  # top-right
        draw.ellipse([x1, y2-2*radius, x1+2*radius, y2], fill=color)  # bottom-left
        draw.ellipse([x2-2*radius, y2-2*radius, x2, y2], fill=color)  # bottom-right
        
        # Outline
        draw.arc([x1, y1, x1+2*radius, y1+2*radius], 180, 270, fill=(0,0,0), width=2)
        draw.arc([x2-2*radius, y1, x2, y1+2*radius], 270, 360, fill=(0,0,0), width=2)
        draw.arc([x1, y2-2*radius, x1+2*radius, y2], 90, 180, fill=(0,0,0), width=2)
        draw.arc([x2-2*radius, y2-2*radius, x2, y2], 0, 90, fill=(0,0,0), width=2)
        draw.line([x1+radius, y1, x2-radius, y1], fill=(0,0,0), width=2)
        draw.line([x1+radius, y2, x2-radius, y2], fill=(0,0,0), width=2)
        draw.line([x1, y1+radius, x1, y2-radius], fill=(0,0,0), width=2)
        draw.line([x2, y1+radius, x2, y2-radius], fill=(0,0,0), width=2)
    
    def _draw_arrow(self, draw: ImageDraw.Draw, position: Tuple[int, int]):
        """Draw a right-pointing arrow."""
        x, y = position
        length = self.config.arrow_length
        
        # Arrow shaft
        draw.line([x-length//2, y, x+length//2-10, y], fill=(0,0,0), width=3)
        
        # Arrow head
        points = [
            (x+length//2, y),
            (x+length//2-15, y-8),
            (x+length//2-15, y+8)
        ]
        draw.polygon(points, fill=(0,0,0))
    
    def _draw_question_mark(self, draw: ImageDraw.Draw, position: Tuple[int, int]):
        """Draw a question mark."""
        x, y = position
        size = self.config.question_mark_size
        
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()
        
        # Get text bounds for centering
        bbox = draw.textbbox((0, 0), "?", font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        
        text_x = x - w // 2
        text_y = y - h // 2
        
        draw.text((text_x, text_y), "?", font=font, fill=(100, 100, 100))
    
    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO GENERATION
    # ══════════════════════════════════════════════════════════════════════════
    
    def _generate_video(self, first_image: Image.Image, final_image: Image.Image, task_id: str, task_data: Dict[str, Any]) -> str:
        """Generate ground truth video showing the transformation."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"
        
        # Create animation frames
        frames = self._create_transformation_frames(first_image, final_image, task_data)
        
        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None
    
    def _create_transformation_frames(self, first_image: Image.Image, final_image: Image.Image, task_data: Dict[str, Any], hold_frames: int = 15, scale_frames: int = 30) -> List[Image.Image]:
        """Create animation frames showing the scaling transformation."""
        frames = []
        
        # Hold initial state
        for _ in range(hold_frames):
            frames.append(first_image.copy())
        
        # Create scaling animation showing the shape gradually changing size
        frames.extend(self._create_scaling_morph_frames(task_data, scale_frames))
        
        # Hold final state
        for _ in range(hold_frames):
            frames.append(final_image.copy())
        
        return frames
    
    def _create_scaling_morph_frames(self, task_data: Dict[str, Any], num_frames: int) -> List[Image.Image]:
        """Create frames showing the shape gradually changing size."""
        frames = []
        
        width, height = self.config.image_size
        margin = self.config.margin
        shape_size = self.config.shape_size
        
        # Position of the shape that's being transformed (bottom right - the answer position)
        answer_x = width - margin - shape_size//2
        answer_y = 3*height//4
        
        shape_c = task_data["shape_c"]
        scale_factor = task_data["scale_factor"]
        
        # Calculate the original size of shape C (same as what's drawn in position C)
        original_size = shape_size  # This is the size used for the original shape C
        target_size = int(shape_size * scale_factor)  # This is the final scaled size
        
        # Ensure target size fits within bounds
        max_allowed_size = self._get_max_shape_size_for_position(answer_x, answer_y)
        target_size = min(target_size, max_allowed_size)
        
        for i in range(num_frames):
            # Create frame with static elements
            img = self.renderer.create_blank_image()
            draw = ImageDraw.Draw(img)
            
            # Draw static elements (A, arrow, B, C, arrow)
            positions = {
                "A": (margin + shape_size//2, height//4),
                "arrow1": (width//2, height//4),
                "B": (width - margin - shape_size//2, height//4),
                "C": (margin + shape_size//2, 3*height//4),
                "arrow2": (width//2, 3*height//4),
            }
            
            # Draw static shapes
            self._draw_shape_at_position(draw, task_data["shape_a"], positions["A"], shape_size, task_data)
            self._draw_arrow(draw, positions["arrow1"])
            self._draw_transformed_shape_at_position(draw, task_data["shape_b"], positions["B"], shape_size, task_data, "B")
            self._draw_shape_at_position(draw, task_data["shape_c"], positions["C"], shape_size, task_data)
            self._draw_arrow(draw, positions["arrow2"])
            
            # Draw scaling shape at answer position
            # Interpolate between original_size and target_size
            scale_progress = i / (num_frames - 1) if num_frames > 1 else 1.0
            current_size = int(original_size + (target_size - original_size) * scale_progress)
            
            self._draw_base_shape(draw, shape_c, answer_x, answer_y, current_size, self.shape_color)
            
            frames.append(img)
        
        return frames
