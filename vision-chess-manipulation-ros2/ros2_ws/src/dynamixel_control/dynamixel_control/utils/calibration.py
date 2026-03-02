import cv2
import numpy as np


class Calibration:
    def __init__(self):
        self.transformation_matrix = None
        self.image_size = None
        self.last_src_corners = None
        self.manual_src_corners = None
    
    def detect_edges(self, raw_image):
        """
        Detects edges from the raw image using Canny edge detection.
        
        Args:
            raw_image: Input image (BGR or grayscale)
        
        Returns:
            Edge detected image (binary)
        """
        # Convert to grayscale if needed
        if len(raw_image.shape) == 3:
            gray = cv2.cvtColor(raw_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = raw_image
        
        # Apply Gaussian blur to reduce noise 필터링
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        return edges
    
    def find_outer_corners(self, edges):
        """
        Finds 4 points in the most outside edge of the chessboard.
        
        Args:
            edges: Edge detected binary image
        
        Returns:
            Four corner points as numpy array [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            Ordered as: top-left, top-right, bottom-right, bottom-left
        """
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            raise ValueError("No contours found in the image")
        
        # Find the largest contour (assumed to be the chessboard)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Approximate the contour to a polygon
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        # If we don't get exactly 4 points, find the convex hull and get extreme points
        if len(approx) != 4:
            # Use convex hull
            hull = cv2.convexHull(largest_contour)
            epsilon = 0.02 * cv2.arcLength(hull, True)
            approx = cv2.approxPolyDP(hull, epsilon, True)
            
            # If still not 4 points, find the 4 extreme corners
            if len(approx) != 4:
                points = largest_contour.reshape(-1, 2)
                
                # Find extreme points
                top_left = points[np.argmin(points.sum(axis=1))]
                bottom_right = points[np.argmax(points.sum(axis=1))]
                top_right = points[np.argmax(points[:, 0] - points[:, 1])]
                bottom_left = points[np.argmin(points[:, 0] - points[:, 1])]
                
                corners = np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
            else:
                corners = approx.reshape(4, 2).astype(np.float32)
        else:
            corners = approx.reshape(4, 2).astype(np.float32)
        
        # Order corners: top-left, top-right, bottom-right, bottom-left
        corners = self._order_points(corners)
        
        return corners
    
    def _order_points(self, pts):
        """
        Orders points in the order: top-left, top-right, bottom-right, bottom-left
        
        Args:
            pts: Array of 4 points
        
        Returns:
            Ordered array of points
        """
        # Initialize ordered coordinates
        rect = np.zeros((4, 2), dtype=np.float32)
        
        # Top-left point has smallest sum, bottom-right has largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right point has smallest difference, bottom-left has largest difference
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect
    
    def create_transformation_matrix(self, raw_image, output_size=None):
        """
        Creates a transformation matrix that straightens the chess plane.
        
        Args:
            raw_image: Input image
            output_size: Tuple (width, height) for output image. If None, uses input size.
        
        Returns:
            Transformation matrix (3x3)
        """
        if self.manual_src_corners is not None:
            src_corners = self.manual_src_corners.copy()
        else:
            # Detect edges
            edges = self.detect_edges(raw_image)
            # Find outer corners
            src_corners = self.find_outer_corners(edges)
        self.last_src_corners = src_corners.copy()
        
        # Determine output image size
        if output_size is None:
            height, width = raw_image.shape[:2]
            output_size = (width, height)
        
        self.image_size = output_size
        
        # Define destination corners (perfect rectangle)
        dst_corners = np.array([
            [0, 0],
            [output_size[0] - 1, 0],
            [output_size[0] - 1, output_size[1] - 1],
            [0, output_size[1] - 1]
        ], dtype=np.float32)
        
        # Calculate perspective transformation matrix
        self.transformation_matrix = cv2.getPerspectiveTransform(src_corners, dst_corners)
        
        return self.transformation_matrix

    def set_manual_corners(self, corners):
        """
        Set source corners manually in order: TL, TR, BR, BL.

        Args:
            corners: list-like with 4 points [[x,y], [x,y], [x,y], [x,y]]
        """
        corners = np.asarray(corners, dtype=np.float32)
        if corners.shape != (4, 2):
            raise ValueError(
                f"manual corners must be shape (4,2), got {corners.shape}"
            )
        self.manual_src_corners = corners
        self.last_src_corners = corners.copy()

    def get_last_corners(self):
        """Returns last detected source corners as Python list."""
        if self.last_src_corners is None:
            return None
        return self.last_src_corners.tolist()

    def draw_last_corners(self, raw_image):
        """Returns image with last detected corners drawn."""
        if self.last_src_corners is None:
            return raw_image.copy()

        debug_image = raw_image.copy()
        labels = ["TL", "TR", "BR", "BL"]
        for idx, point in enumerate(self.last_src_corners):
            x, y = int(point[0]), int(point[1])
            cv2.circle(debug_image, (x, y), 8, (0, 0, 255), -1)
            cv2.putText(
                debug_image,
                f"{labels[idx]}({x},{y})",
                (x + 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )
        return debug_image
    
    def apply_transformation(self, raw_image):
        """
        Applies the transformation matrix to straighten the chess plane.
        
        Args:
            raw_image: Input image
        
        Returns:
            Straightened image
        """
        if self.transformation_matrix is None:
            raise ValueError("Transformation matrix not created. Call create_transformation_matrix first.")
        
        # Apply perspective transformation
        straightened = cv2.warpPerspective(
            raw_image, 
            self.transformation_matrix, 
            self.image_size
        )
        
        return straightened
    
    def calibrate(self, raw_image, output_size=None):
        """
        Complete calibration pipeline: creates transformation matrix and applies it.
        
        Args:
            raw_image: Input image
            output_size: Tuple (width, height) for output image. If None, uses input size.
        
        Returns:
            Straightened image
        """
        # Create transformation matrix
        self.create_transformation_matrix(raw_image, output_size)
        
        # Apply transformation
        straightened = self.apply_transformation(raw_image)
        
        return straightened
