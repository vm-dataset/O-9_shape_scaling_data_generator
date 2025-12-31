"""Video generation utilities."""

import math
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw
import tempfile

# Try to import cv2
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️  Warning: opencv-python not installed. Video generation disabled.")
    print("   Install with: pip install opencv-python==4.8.1.78")


class VideoGenerator:
    """Generate videos from image sequences."""
    
    def __init__(self, fps: int = 10, codec: str = 'XVID'):
        """
        Initialize video generator.
        
        Args:
            fps: Frames per second
            codec: Video codec (XVID, MJPG, etc.)
        """
        self.fps = fps
        self.codec = codec
        
        if not CV2_AVAILABLE:
            raise ImportError("opencv-python is required for video generation")
    
    def create_video_from_frames(
        self,
        frames: List[Image.Image],
        output_path: Path,
        size: Optional[Tuple[int, int]] = None
    ) -> Path:
        """
        Create AVI video from PIL Image frames.
        
        Args:
            frames: List of PIL Images
            output_path: Path to save video
            size: Optional (width, height) tuple. If None, uses first frame size
            
        Returns:
            Path to created video file
        """
        if not frames:
            raise ValueError("No frames provided")
        
        # Get video size
        if size is None:
            size = frames[0].size
        
        width, height = size
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            self.fps,
            (width, height)
        )
        
        # Write frames
        for frame in frames:
            # Ensure RGB and correct size
            if frame.size != size:
                frame = frame.resize(size, Image.Resampling.LANCZOS)
            
            # Convert PIL Image to OpenCV format (BGR)
            frame_rgb = frame.convert('RGB')
            frame_array = np.array(frame_rgb)
            frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            
            writer.write(frame_bgr)
        
        writer.release()
        return output_path
    
    def interpolate_frames(
        self,
        start_frame: Image.Image,
        end_frame: Image.Image,
        num_intermediate: int = 10
    ) -> List[Image.Image]:
        """
        Create smooth transition between two frames using alpha blending.
        
        Args:
            start_frame: Initial frame
            end_frame: Final frame
            num_intermediate: Number of intermediate frames to generate
            
        Returns:
            List of frames including start, intermediates, and end
        """
        frames = [start_frame]
        
        # Ensure same size and mode
        if start_frame.size != end_frame.size:
            end_frame = end_frame.resize(start_frame.size, Image.Resampling.LANCZOS)
        
        start_frame = start_frame.convert('RGBA')
        end_frame = end_frame.convert('RGBA')
        
        # Generate intermediate frames
        for i in range(1, num_intermediate + 1):
            alpha = i / (num_intermediate + 1)
            blended = Image.blend(start_frame, end_frame, alpha)
            frames.append(blended.convert('RGB'))
        
        frames.append(end_frame.convert('RGB'))
        return frames


class ChessVideoGenerator:
    """Generate videos specifically for chess moves."""
    
    def __init__(self, fps: int = 10):
        self.fps = fps
        self.video_gen = VideoGenerator(fps=fps) if CV2_AVAILABLE else None
    
    def generate_move_video(
        self,
        initial_board_image: Image.Image,
        final_board_image: Image.Image,
        from_square: Tuple[int, int],
        to_square: Tuple[int, int],
        output_path: Path,
        num_frames: int = 15
    ) -> Optional[Path]:
        """
        Generate video showing a chess piece moving with highlight overlay.
        
        Args:
            initial_board_image: Board before move
            final_board_image: Board after move
            from_square: (file, rank) tuple for starting square (0-7)
            to_square: (file, rank) tuple for ending square (0-7)
            output_path: Path to save video
            num_frames: Total number of frames for the move
            
        Returns:
            Path to video file, or None if cv2 not available
        """
        if not CV2_AVAILABLE or self.video_gen is None:
            return None
        
        frames = []
        width, height = initial_board_image.size
        square_size = width // 8
        
        # Calculate pixel positions for square centers
        from_x = from_square[0] * square_size
        from_y = (7 - from_square[1]) * square_size
        to_x = to_square[0] * square_size
        to_y = (7 - to_square[1]) * square_size
        
        # Phase 1: Hold initial position with highlight (3 frames)
        for _ in range(3):
            frame = initial_board_image.copy()
            frame = self._draw_square_highlight(frame, from_x, from_y, square_size, (255, 255, 0, 120))
            frames.append(frame)
        
        # Phase 2: Movement animation with both squares highlighted (num_frames)
        for i in range(num_frames):
            t = i / (num_frames - 1) if num_frames > 1 else 1.0
            
            frame = initial_board_image.copy()
            
            # Highlight from square (fading out)
            alpha_from = int(120 * (1 - t))
            frame = self._draw_square_highlight(frame, from_x, from_y, square_size, (255, 255, 0, alpha_from))
            
            # Highlight to square (fading in)
            alpha_to = int(120 * t)
            frame = self._draw_square_highlight(frame, to_x, to_y, square_size, (0, 255, 0, alpha_to))
            
            # Draw movement arrow
            frame = self._draw_arrow(frame, 
                                    (from_x + square_size//2, from_y + square_size//2),
                                    (to_x + square_size//2, to_y + square_size//2),
                                    (255, 0, 0, 200))
            
            frames.append(frame)
        
        # Phase 3: Show final position with highlight (5 frames)
        for _ in range(5):
            frame = final_board_image.copy()
            frame = self._draw_square_highlight(frame, to_x, to_y, square_size, (0, 255, 0, 120))
            frames.append(frame)
        
        # Phase 4: Hold final position without highlight (3 frames)
        for _ in range(3):
            frames.append(final_board_image.copy())
        
        # Create video
        return self.video_gen.create_video_from_frames(frames, output_path)
    
    def _draw_square_highlight(
        self,
        image: Image.Image,
        x: int,
        y: int,
        size: int,
        color: Tuple[int, int, int, int]
    ) -> Image.Image:
        """Draw semi-transparent square highlight overlay."""
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        draw.rectangle(
            [x, y, x + size, y + size],
            fill=color,
            outline=(color[0], color[1], color[2], 255),
            width=3
        )
        
        base = image.convert('RGBA')
        return Image.alpha_composite(base, overlay).convert('RGB')
    
    def _draw_arrow(
        self,
        image: Image.Image,
        start: Tuple[int, int],
        end: Tuple[int, int],
        color: Tuple[int, int, int, int]
    ) -> Image.Image:
        """Draw arrow from start to end position."""
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw line
        draw.line([start, end], fill=color, width=4)
        
        # Draw arrowhead
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        arrow_length = 20
        arrow_angle = math.pi / 6
        
        point1 = (
            int(end[0] - arrow_length * math.cos(angle - arrow_angle)),
            int(end[1] - arrow_length * math.sin(angle - arrow_angle))
        )
        point2 = (
            int(end[0] - arrow_length * math.cos(angle + arrow_angle)),
            int(end[1] - arrow_length * math.sin(angle + arrow_angle))
        )
        
        draw.polygon([end, point1, point2], fill=color)
        
        base = image.convert('RGBA')
        return Image.alpha_composite(base, overlay).convert('RGB')
    
    def generate_simple_video(
        self,
        initial_board_image: Image.Image,
        final_board_image: Image.Image,
        output_path: Path,
        hold_frames: int = 5,
        transition_frames: int = 15
    ) -> Optional[Path]:
        """
        Generate simple video with smooth cross-fade transition.
        
        Args:
            initial_board_image: Board before move
            final_board_image: Board after move
            output_path: Path to save video
            hold_frames: Frames to hold at start and end
            transition_frames: Frames for transition
            
        Returns:
            Path to video file, or None if cv2 not available
        """
        if not CV2_AVAILABLE or self.video_gen is None:
            return None
        
        frames = []
        
        # Hold initial position
        for _ in range(hold_frames):
            frames.append(initial_board_image.copy())
        
        # Smooth cross-fade transition
        initial_rgba = initial_board_image.convert('RGBA')
        final_rgba = final_board_image.convert('RGBA')
        
        for i in range(transition_frames):
            alpha = i / (transition_frames - 1) if transition_frames > 1 else 1.0
            blended = Image.blend(initial_rgba, final_rgba, alpha)
            frames.append(blended.convert('RGB'))
        
        # Hold final position
        for _ in range(hold_frames):
            frames.append(final_board_image.copy())
        
        # Create video
        return self.video_gen.create_video_from_frames(frames, output_path)

