from direct.task import Task
from panda3d.core import Vec3
import math


class OrbitCamera:
    
    def __init__(self, showbase, camera, mouse_watcher):
        self.showbase = showbase
        self.camera = camera
        self.mouse_watcher = mouse_watcher
        
        # Target (look-at) and spherical camera params
        self._target = Vec3(0, 0, 0)
        # Initial values will be set by set_optimal_view, so start with reasonable defaults
        self._distance = 15.0         # temporary default, will be overridden
        self._yaw = math.radians(-30)  # left/right
        self._pitch = math.radians(25)  # up/down (clamped) - will be adjusted by set_optimal_view
        self._min_pitch = math.radians(-85)
        self._max_pitch = math.radians(85)
        self._min_dist = 5.0          # increased minimum distance
        self._max_dist = 80.0         # increased maximum distance for larger objects

        # Drag state
        self._dragging = False
        self._last_mouse = None
        self._yaw_sensitivity = 1.5    # degrees per normalized-screen unit
        self._pitch_sensitivity = 1.2
        self._zoom_step = 1.1          # scroll multiplier

        # place camera initially
        self._update_camera()

        # mouse events
        self.showbase.accept("mouse1", self._start_drag)
        self.showbase.accept("mouse1-up", self._end_drag)
        self.showbase.accept("wheel_up", self._zoom_in)
        self.showbase.accept("wheel_down", self._zoom_out)

    def setup_task(self, task_mgr):
        task_mgr.add(self._mouse_task, "orbit-mouse-task", sort=10)

    def _start_drag(self):
        if self.mouse_watcher.hasMouse():
            m = self.mouse_watcher.getMouse()  # (-1..1, -1..1)
            self._last_mouse = (m.getX(), m.getY())
            self._dragging = True

    def _end_drag(self):
        self._dragging = False
        self._last_mouse = None

    def _zoom_in(self):
        self._distance = max(self._min_dist, self._distance / self._zoom_step)
        self._update_camera()

    def _zoom_out(self):
        self._distance = min(self._max_dist, self._distance * self._zoom_step)
        self._update_camera()

    def _mouse_task(self, task: Task):
        if self._dragging and self.mouse_watcher.hasMouse():
            m = self.mouse_watcher.getMouse()
            x, y = m.getX(), m.getY()
            if self._last_mouse is not None:
                dx = x - self._last_mouse[0]
                dy = y - self._last_mouse[1]
                # convert to radians; screen units are ~[-1,1]
                self._yaw   -= math.radians(dx * 180 * self._yaw_sensitivity)
                self._pitch -= math.radians(dy * 180 * self._pitch_sensitivity)
                # clamp pitch to avoid flipping
                self._pitch = max(self._min_pitch, min(self._max_pitch, self._pitch))
                self._update_camera()
            self._last_mouse = (x, y)
        return Task.cont

    def _update_camera(self):
        # spherical to cartesian around target
        r = self._distance
        cp = math.cos(self._pitch)
        x = r * cp * math.sin(self._yaw)
        y = -r * cp * math.cos(self._yaw)  # negative so yaw=0 looks toward -Y
        z = r * math.sin(self._pitch)

        self.camera.setPos(self._target + Vec3(x, y, z))
        self.camera.lookAt(self._target)



    def set_target(self, target_pos):
        self._target = target_pos
        self._update_camera()

    def get_target(self):
        return self._target

    def set_distance_for_object_height(self, object_height):

        base_distance = 8.0  # Minimum comfortable viewing distance
        optimal_distance = max(base_distance, object_height * 4.0)
        
        # Keep it within our min/max bounds
        self._distance = max(self._min_dist, min(self._max_dist, optimal_distance))
        self._update_camera()
    
    def set_optimal_view(self, object_height, object_diameter=None):
        # Calculate optimal distance based on object size
        if object_diameter:
            # Consider both height and width for better framing
            size_factor = max(object_height, object_diameter)
        else:
            size_factor = object_height
        
        # Set distance with good framing
        base_distance = 10.0  # Comfortable viewing distance
        optimal_distance = max(base_distance, size_factor * 3.5)
        self._distance = max(self._min_dist, min(self._max_dist, optimal_distance))
        
        # Adjust pitch for better perspective based on object proportions
        if object_diameter and object_height:
            aspect_ratio = object_height / object_diameter
            if aspect_ratio > 2.0:  # Tall, thin object
                self._pitch = math.radians(30)  # Higher angle to see top
            elif aspect_ratio < 0.5:  # Wide, short object
                self._pitch = math.radians(15)  # Lower angle to see width
            else:  # Balanced proportions
                self._pitch = math.radians(25)
        
        self._update_camera()
    
    def reset_to_default_view(self):
        # Use the same values as the initial setup for consistency
        self._distance = 15.0
        self._yaw = math.radians(-30)
        self._pitch = math.radians(25)
        self._update_camera()
