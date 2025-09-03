# Panda3D base app class that handles windows, scenes, and rendering
from direct.showbase.ShowBase import ShowBase

# Panda3D node that contains the geometry
from panda3d.core import GeomNode

# Importing geometry from the new organized structure
from src.geometry.vase.geometry import vaseGeometry
from src.geometry.table.geometry import tableGeometry

from src.geometry.vase.config import vaseSliderConfig, vaseDefaults
from src.geometry.table.config import tableSliderConfig, tableDefaults
from src.rendering.lighting import setup_lights

# Script that builds sliders and handles changes
from src.ui.controls import ParametricControls

# UI metrics for simple on-screen labels
from src.ui.ui_metrics import UIMetrics

# Camera controller that handles the camera's movement and rotation
from src.camera.controller import OrbitCamera

# Import for better architecture and performance
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from functools import lru_cache
import time
import weakref

## ATTEMPT TO MAKE THE PROGRAM RUN AS FAST AS POSSIBLE

# ============================================================================
# PERFORMANCE OPTIMIZATION CONSTANTS
# ============================================================================

# Debounce timing for parameter updates (milliseconds)
PARAMETER_UPDATE_DEBOUNCE = 100  # 100ms delay before rebuilding

# Cache sizes for LRU caches
GEOMETRY_CACHE_SIZE = 128  # Cache up to 128 different geometry configurations
DISPLAY_CACHE_SIZE = 64    # Cache display calculations

# Batch update threshold
BATCH_UPDATE_THRESHOLD = 3  # Update after 3 parameter changes


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class GeometryResult:
    object_type: str
    geometry: Any
    height: float
    diameter: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ObjectCreationRequest:
    params: Dict[str, Any]
    object_type: str
    position: Tuple[float, float, float] = (0, 0, 0)
    scale: float = 1.0


@dataclass
class CachedGeometry:
    geometry_result: GeometryResult
    timestamp: float
    access_count: int = 0


# ============================================================================
# INTERFACES (CONTRACTS)
# ============================================================================

class GeometryProvider(ABC):
    
    @abstractmethod
    def create_geometry(self, params: Dict[str, Any]) -> GeometryResult:
        pass
    
    @abstractmethod
    def get_supported_parameters(self) -> Dict[str, Any]:
        pass


class SceneObjectFactory(ABC):
    
    @abstractmethod
    def create_scene_object(self, request: ObjectCreationRequest, geometry_result: GeometryResult) -> Any:
        pass


class ObjectDisplayManager(ABC):
    
    @abstractmethod
    def update_display(self, object_np: Any, geometry_result: GeometryResult) -> None:
        pass


# ============================================================================
# PERFORMANCE OPTIMIZED IMPLEMENTATIONS
# ============================================================================

class OptimizedVaseGeometryProvider(GeometryProvider):
    
    def __init__(self):
        # Pre-import to avoid dynamic imports in hot path
        from src.geometry.vase.geometry import vaseGeometry
        from src.geometry.vase.config import vaseDefaults
        self._vaseGeometry = vaseGeometry
        self._vaseDefaults = vaseDefaults
        
        # Cache for geometry results
        self._geometry_cache: Dict[str, CachedGeometry] = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def create_geometry(self, params: Dict[str, Any]) -> GeometryResult:
        # Create cache key from parameters
        cache_key = self._create_cache_key(params)
        
        # Check cache first
        cached = self._geometry_cache.get(cache_key)
        if cached:
            self._cache_hits += 1
            cached.access_count += 1
            cached.timestamp = time.time()
            return cached.geometry_result
        
        # Cache miss - create new geometry
        self._cache_misses += 1
        result = self._vaseGeometry(
            segment_count=int(params["Segment Count"]),
            object_width=params["Object Width"],
            twist_angle=params["Twist Angle"],
            twist_groove_depth=params["Twist Groove Depth"],
            vertical_wave_freq=params["Vertical Wave Frequency"],
            vertical_wave_depth=params["Vertical Wave Depth"]
        )
        
        geometry_result = self._extract_result(result, "Vace")
        
        # Cache the result
        self._cache_geometry(cache_key, geometry_result)
        
        return geometry_result
    
    def get_supported_parameters(self) -> Dict[str, Any]:
        return self._vaseDefaults()
    
    def _create_cache_key(self, params: Dict[str, Any]) -> str:
        # Round parameters to reduce cache fragmentation
        rounded_params = {
            "Segment Count": int(params["Segment Count"]),
            "Object Width": round(params["Object Width"], 2),
            "Twist Angle": round(params["Twist Angle"], 2),
            "Twist Groove Depth": round(params["Twist Groove Depth"], 3),
            "Vertical Wave Frequency": round(params["Vertical Wave Frequency"], 2),
            "Vertical Wave Depth": round(params["Vertical Wave Depth"], 3)
        }
        return str(sorted(rounded_params.items()))
    
    def _cache_geometry(self, key: str, geometry_result: GeometryResult):
        """Cache geometry result with LRU eviction."""
        if len(self._geometry_cache) >= GEOMETRY_CACHE_SIZE:
            # Remove least recently used
            oldest_key = min(self._geometry_cache.keys(), 
                           key=lambda k: self._geometry_cache[k].timestamp)
            del self._geometry_cache[oldest_key]
        
        self._geometry_cache[key] = CachedGeometry(
            geometry_result=geometry_result,
            timestamp=time.time()
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_size": len(self._geometry_cache),
            "hit_rate": self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0
        }
    
    def _extract_result(self, result, object_type: str) -> GeometryResult:
        if isinstance(result, tuple) and len(result) >= 2:
            actual_type = result[0]
            geom = result[1]
            height = result[2] if len(result) > 2 else 2.0
            diameter = result[3] if len(result) > 3 else None
        else:
            actual_type = object_type
            geom = result
            height = 2.0
            diameter = None
        
        return GeometryResult(
            object_type=actual_type,
            geometry=geom,
            height=height,
            diameter=diameter
        )


class OptimizedTableGeometryProvider(GeometryProvider):
    
    def __init__(self):
        from src.geometry.table.geometry import tableGeometry
        from src.geometry.table.config import tableDefaults
        self._tableGeometry = tableGeometry
        self._tableDefaults = tableDefaults
        
        # Cache for geometry results
        self._geometry_cache: Dict[str, CachedGeometry] = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def create_geometry(self, params: Dict[str, Any]) -> GeometryResult:
        # Create cache key from parameters
        cache_key = self._create_cache_key(params)
        
        # Check cache first
        cached = self._geometry_cache.get(cache_key)
        if cached:
            self._cache_hits += 1
            cached.access_count += 1
            cached.timestamp = time.time()
            return cached.geometry_result
        
        self._cache_misses += 1
        result = self._tableGeometry(
            segment_count=int(params["Segment Count"]),
            object_width=params["Object Width"],
            twist_angle=params["Twist Angle"],
            twist_groove_depth=params["Twist Groove Depth"],
            vertical_wave_freq=params["Vertical Wave Frequency"],
            vertical_wave_depth=params["Vertical Wave Depth"]
        )
        
        geometry_result = self._extract_result(result, "Table")
        
        # Cache the result
        self._cache_geometry(cache_key, geometry_result)
        
        return geometry_result
    
    def get_supported_parameters(self) -> Dict[str, Any]:
        return self._tableDefaults()
    
    def _create_cache_key(self, params: Dict[str, Any]) -> str:
        rounded_params = {
            "Segment Count": int(params["Segment Count"]),
            "Object Width": round(params["Object Width"], 2),
            "Twist Angle": round(params["Twist Angle"], 2),
            "Twist Groove Depth": round(params["Twist Groove Depth"], 3),
            "Vertical Wave Frequency": round(params["Vertical Wave Frequency"], 2),
            "Vertical Wave Depth": round(params["Vertical Wave Depth"], 3)
        }
        return str(sorted(rounded_params.items()))
    
    def _cache_geometry(self, key: str, geometry_result: GeometryResult):
        if len(self._geometry_cache) >= GEOMETRY_CACHE_SIZE:
            # Remove least recently used
            oldest_key = min(self._geometry_cache.keys(), 
                           key=lambda k: self._geometry_cache[k].timestamp)
            del self._geometry_cache[oldest_key]
        
        self._geometry_cache[key] = CachedGeometry(
            geometry_result=geometry_result,
            timestamp=time.time()
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_size": len(self._geometry_cache),
            "hit_rate": self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0
        }
    
    def _extract_result(self, result, object_type: str) -> GeometryResult:
        if isinstance(result, tuple) and len(result) >= 2:
            actual_type = result[0]
            geom = result[1]
            height = result[2] if len(result) > 2 else 2.0
            diameter = result[3] if len(result) > 3 else None
        else:
            actual_type = object_type
            geom = result
            height = 2.0
            diameter = None
        
        return GeometryResult(
            object_type=actual_type,
            geometry=geom,
            height=height,
            diameter=diameter
        )


class ObjectFactory(SceneObjectFactory):
    
    def __init__(self):
        self.render = None
        self._node_pool = []
        self._pool_size = 32
    
    def create_scene_object(self, request: ObjectCreationRequest, geometry_result: GeometryResult) -> Any:
        # Try to reuse a node from the pool
        if self._node_pool:
            node = self._node_pool.pop()
            node.removeAllGeoms()  # Clear existing geometry
        else:
            node = GeomNode(f"object_{request.object_type}")
        
        # Add new geometry
        node.addGeom(geometry_result.geometry)
        
        # Attach to scene
        object_np = self.render.attachNewNode(node)
        object_np.setPos(request.position)
        object_np.setScale(request.scale)
        
        return object_np
    
    def recycle_node(self, node):
        if len(self._node_pool) < self._pool_size:
            self._node_pool.append(node)


class OptimizedMainObjectDisplayManager(ObjectDisplayManager):
    
    def __init__(self, ui_metrics, camera_controller):
        self.ui_metrics = ui_metrics
        self.camera_controller = camera_controller
        self._last_update_time = 0
        self._pending_updates = 0
        self._display_cache = {}
    
    def update_display(self, object_np: Any, geometry_result: GeometryResult) -> None:  
        current_time = time.time()
        
        # Debounce rapid updates
        if current_time - self._last_update_time < (PARAMETER_UPDATE_DEBOUNCE / 1000.0):
            self._pending_updates += 1
            return
        
        # Batch update if we have multiple pending updates
        if self._pending_updates > 0:
            self._pending_updates = 0
        
        # Check display cache
        cache_key = self._create_display_cache_key(geometry_result)
        if cache_key in self._display_cache:
            # Use cached display data
            cached_data = self._display_cache[cache_key]
            self._apply_cached_display(cached_data, object_np)
        else:
            # Calculate new display data
            display_data = self._calculate_display_data(object_np, geometry_result)
            self._cache_display_data(cache_key, display_data)
            self._apply_display_data(display_data, object_np)
        
        self._last_update_time = current_time
    
    def _create_display_cache_key(self, geometry_result: GeometryResult) -> str:
        return f"{geometry_result.object_type}_{geometry_result.height}_{geometry_result.diameter}"
    
    def _calculate_display_data(self, object_np: Any, geometry_result: GeometryResult) -> Dict[str, Any]:
        display_data = {
            'ui_metrics': None,
            'camera_distance': None
        }
        
        # Calculate UI metrics
        if self.ui_metrics:
            if geometry_result.diameter is not None:
                display_data['ui_metrics'] = {
                    'type': 'diameter_height',
                    'diameter': geometry_result.diameter,
                    'height': geometry_result.height
                }
            else:
                # Calculate bounds as fallback
                bounds = object_np.getBounds()
                if not bounds.isEmpty():
                    min_pt = bounds.getMin()
                    max_pt = bounds.getMax()
                    width = max_pt.getX() - min_pt.getX()
                    height_val = max_pt.getZ() - min_pt.getZ()
                    depth = max_pt.getY() - min_pt.getY()
                    display_data['ui_metrics'] = {
                        'type': 'bounds',
                        'width': width,
                        'height': height_val,
                        'depth': depth
                    }
        
        # Calculate camera distance
        if self.camera_controller:
            display_data['camera_distance'] = geometry_result.height
        
        return display_data
    
    def _cache_display_data(self, key: str, data: Dict[str, Any]):
        if len(self._display_cache) >= DISPLAY_CACHE_SIZE:
            # Remove oldest entry
            oldest_key = min(self._display_cache.keys(), 
                           key=lambda k: self._display_cache[k].get('timestamp', 0))
            del self._display_cache[oldest_key]
        
        data['timestamp'] = time.time()
        self._display_cache[key] = data
    
    def _apply_cached_display(self, cached_data: Dict[str, Any], object_np: Any):
        self._apply_display_data(cached_data, object_np)
    
    def _apply_display_data(self, display_data: Dict[str, Any], object_np: Any):
        # Update UI metrics
        if self.ui_metrics and display_data['ui_metrics']:
            metrics = display_data['ui_metrics']
            if metrics['type'] == 'diameter_height':
                self.ui_metrics.show_bounding_box(
                    diameter=metrics['diameter'], 
                    height=metrics['height']
                )
            elif metrics['type'] == 'bounds':
                self.ui_metrics.show_bounding_box(
                    width=metrics['width'],
                    height=metrics['height'],
                    depth=metrics['depth']
                )
        
        # Adjust camera to optimal view
        if self.camera_controller and display_data['camera_distance']:
            if display_data['ui_metrics'] and display_data['ui_metrics'].get('diameter'):
                print(f"Parameter change camera view: height={display_data['camera_distance']:.2f}, diameter={display_data['ui_metrics']['diameter']:.2f}")
                self.camera_controller.set_optimal_view(
                    display_data['camera_distance'], 
                    display_data['ui_metrics']['diameter']
                )
            else:
                print(f"Parameter change camera view: height={display_data['camera_distance']:.2f}, no diameter")
                self.camera_controller.set_optimal_view(display_data['camera_distance'])


# ============================================================================
# PERFORMANCE OPTIMIZED SERVICE LAYER
# ============================================================================

class OptimizedObjectCreationService:
    
    def __init__(self, scene_factory: SceneObjectFactory, display_manager: ObjectDisplayManager):
        self.scene_factory = scene_factory
        self.display_manager = display_manager
        self.geometry_providers = {
            "Vace": OptimizedVaseGeometryProvider(),
            "Table": OptimizedTableGeometryProvider()
        }
        
        # Performance monitoring
        self._creation_times = []
        self._total_creations = 0
    
    def create_object(self, request: ObjectCreationRequest) -> Any:
        start_time = time.time()
        
        # Get the appropriate geometry provider
        provider = self.geometry_providers.get(request.object_type)
        if not provider:
            raise ValueError(f"Unsupported object type: {request.object_type}")
        
        # Create geometry
        geometry_result = provider.create_geometry(request.params)
        
        # Create scene object using the geometry result
        scene_object = self.scene_factory.create_scene_object(request, geometry_result)
        
        # Update display if this is the main object
        if request.position == (0, 0, 0):
            self.display_manager.update_display(scene_object, geometry_result)
        
        # Record performance metrics
        creation_time = time.time() - start_time
        self._creation_times.append(creation_time)
        self._total_creations += 1
        
        # Keep only last 100 measurements
        if len(self._creation_times) > 100:
            self._creation_times.pop(0)
        
        return scene_object
    
    def get_geometry_provider(self, object_type: str) -> GeometryProvider:
        return self.geometry_providers.get(object_type)
    
    def get_supported_object_types(self) -> list:
        return list(self.geometry_providers.keys())
    
    def get_performance_stats(self) -> Dict[str, Any]:
        if not self._creation_times:
            return {}
        
        return {
            "total_creations": self._total_creations,
            "avg_creation_time": sum(self._creation_times) / len(self._creation_times),
            "min_creation_time": min(self._creation_times),
            "max_creation_time": max(self._creation_times),
            "recent_creations": len(self._creation_times)
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        stats = {}
        for name, provider in self.geometry_providers.items():
            if hasattr(provider, 'get_cache_stats'):
                stats[name] = provider.get_cache_stats()
        return stats


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class MainApp(ShowBase):


    def __init__(self):
        # Initialize Panda3D engine
        super().__init__()
        
        # Disable default mouse controls (we use custom camera)
        self.disableMouse()
        
        # Initialize application state
        self._init_application_state()
        
        # Initialize optimized services
        self._init_optimized_services()
        
        # Setup camera controls FIRST (before building scene)
        self._setup_camera_orbit()
        
        # Build the initial 3D scene
        self._build_initial_scene()
        
        # Setup remaining interactive systems
        self._setup_interactive_systems()
        
        ##### BEEN TRYING DIFFERENT WYAS TO MAKE THE PROGRAM RUN AS FAST AS POSSIBLE
        # Performance monitoring
        self._performance_monitor = PerformanceMonitor()

    # ============================================================================
    # INITIALIZATION METHODS
    # ============================================================================

    def _init_application_state(self):
        # Set default object type and parameters
        self.current_object_type = "Vace"
        self.current_params = vaseDefaults()
        
        # Initialize UI components
        self.ui_metrics = UIMetrics()
        
        # Initialize favorites system
        self.favorites_list = []
        self.current_favorite_index = 0
        self.favorite_objects = []
        
        # Performance optimization: batch parameter updates
        self._pending_parameter_updates = {}
        self._last_parameter_update_time = 0

    def _init_optimized_services(self):
        # Create optimized display manager
        self.display_manager = OptimizedMainObjectDisplayManager(self.ui_metrics, None)
        
        # Create optimized scene factory
        self.scene_factory = ObjectFactory()
        self.scene_factory.render = self.render
        
        # Create optimized object creation service
        self.object_service = OptimizedObjectCreationService(self.scene_factory, self.display_manager)

    def _build_initial_scene(self):
        # Create the main 3D object
        self.build_object()
        
        # Setup lighting
        setup_lights(self.render)
        
        # Set initial camera view AFTER object is created
        self._set_initial_camera_view()

    def _setup_interactive_systems(self):
        # Update display manager with camera controller (already created)
        self.display_manager.camera_controller = self.camera_controller
        
        # Setup user interface
        self._setup_ui()

    # ============================================================================
    # PERFORMANCE OPTIMIZED OBJECT MANAGEMENT
    # ============================================================================

    def build_object(self):
        # Remove existing object if it exists
        if hasattr(self, 'cylinder_np'):
            # Recycle the node for reuse
            if hasattr(self.scene_factory, 'recycle_node'):
                self.scene_factory.recycle_node(self.cylinder_np.node())
            self.cylinder_np.removeNode()

        # Create request for object creation
        request = ObjectCreationRequest(
            params=self.current_params,
            object_type=self.current_object_type,
            position=(0, 0, 0),
            scale=1.0
        )
        
        # Create new object using optimized service
        self.cylinder_np = self.object_service.create_object(request)

    def _create_object_with_params(self, params, object_type="Vace", position=(0, 0, 0), scale=1):
        # Create request
        request = ObjectCreationRequest(
            params=params,
            object_type=object_type,
            position=position,
            scale=scale
        )
        
        # Use optimized service to create object
        return self.object_service.create_object(request)

    # ============================================================================
    # PERFORMANCE OPTIMIZED PARAMETER HANDLING
    # ============================================================================

    def _on_parameters_change(self, params):
        current_time = time.time()
        
        # Batch parameter updates
        self._pending_parameter_updates.update(params)
        
        # Debounce rapid updates
        if current_time - self._last_parameter_update_time < (PARAMETER_UPDATE_DEBOUNCE / 1000.0):
            return
        
        # Apply all pending updates at once
        self.current_params.update(self._pending_parameter_updates)
        self._pending_parameter_updates.clear()
        self._last_parameter_update_time = current_time
        
        # Rebuild object
        self.build_object()

    # ============================================================================
    # CAMERA SYSTEM
    # ============================================================================

    def _setup_camera_orbit(self):
        self.camera_controller = OrbitCamera(self, self.cam, self.mouseWatcherNode)
        self.camera_controller.setup_task(self.taskMgr)
    
    def _set_initial_camera_view(self):
        if hasattr(self, 'cylinder_np') and self.camera_controller:
            # Get object dimensions for optimal framing
            bounds = self.cylinder_np.getBounds()
            if not bounds.isEmpty():
                min_pt = bounds.getMin()
                max_pt = bounds.getMax()
                height = max_pt.getZ() - min_pt.getZ()
                width = max_pt.getX() - min_pt.getX()
                depth = max_pt.getY() - min_pt.getY()
                diameter = max(width, depth)
                
                self.camera_controller.set_optimal_view(height, diameter)
                
                print(f"Initial camera view: height={height:.2f}, diameter={diameter:.2f}")
            else:
                # Fallback to default view
                self.camera_controller.reset_to_default_view()
                print("Using fallback camera view (no bounds)")
        else:
            print("Cannot set initial camera view: missing cylinder_np or camera_controller")

    # ============================================================================
    # USER INTERFACE
    # ============================================================================

    def _setup_ui(self):
        self.parametric_controls = ParametricControls(
            on_parameter_change_callback=self._on_parameters_change,
            slider_config_func=vaseSliderConfig,
            on_object_change_callback=self._on_object_change,
            get_current_object_type_callable=lambda: self.current_object_type,
            on_hide_object_callback=self._hide_object,
            on_show_object_callback=self._show_object,
            on_rebuild_with_params_callback=self._rebuild_with_params,
            on_display_all_favorites_callback=self._display_all_favorites,
            on_clear_favorite_objects_callback=self._clear_favorite_objects,
            on_highlight_favorite_callback=self._highlight_favorite
        )

    def _on_object_change(self, selected_object_type: str):
        self.current_object_type = selected_object_type
        
        # Get new defaults from the appropriate provider
        provider = self.object_service.get_geometry_provider(selected_object_type)
        if provider:
            defaults = provider.get_supported_parameters()
            
            # Update application state
            self.current_params.update(defaults)
            
            # Update UI controls
            if hasattr(self, 'parametric_controls'):
                self.parametric_controls.reset_to_defaults(selected_object_type)
            
            # Rebuild object with new defaults
            self.build_object()

    def _hide_object(self):
        if hasattr(self, 'cylinder_np'):
            self.cylinder_np.hide()

    def _show_object(self):
        if hasattr(self, 'cylinder_np'):
            self.cylinder_np.show()

    def _rebuild_with_params(self, params, object_type=None):
        if object_type:
            self.current_object_type = object_type
        self.current_params.update(params)
        self.build_object()

    # ============================================================================
    # FAVORITES SYSTEM
    # ============================================================================

    def _display_all_favorites(self, favorites_list):
        # Clear existing favorites
        self._clear_favorite_objects_from_scene()
        
        if not favorites_list:
            return
        
        # Setup favorites display
        self.favorites_list = favorites_list
        self.current_favorite_index = 0
        
        # Display favorites and setup camera (FINALLY FOUND THE ERROR)                    THIS WAS THE PROBLEM!!!!!!!!
        self._display_favorites_grid()
        self._focus_camera_on_current_favorite()
        
        # Update UI
        if hasattr(self, 'parametric_controls'):
            self.parametric_controls.set_favorites_list(favorites_list)

    def _display_favorites_grid(self):
        if not self.favorites_list:
            return
        
        # Calculate layout
        total_favorites = len(self.favorites_list)
        spacing = 4.0
        start_x = -(total_favorites - 1) * spacing / 2
        
        # Create objects
        for i, favorite in enumerate(self.favorites_list):
            x = start_x + i * spacing
            params = favorite.get("parameters", {})
            object_type = favorite.get("object_type", "Vace")
            
            obj_np = self._create_object_with_params(
                params, object_type, position=(x, 0, 0), scale=1.0
            )
            self.favorite_objects.append(obj_np)

    def _focus_camera_on_current_favorite(self):
        if not self.favorites_list:
            return
        
        # Calculate target position
        total_favorites = len(self.favorites_list)
        spacing = 4.0
        start_x = -(total_favorites - 1) * spacing / 2
        target_x = start_x + self.current_favorite_index * spacing
        
        # Store original camera state
        self._store_original_camera_state()
        
        # Focus camera on target
        if hasattr(self, 'camera_controller'):
            from panda3d.core import Vec3
            self.camera_controller.set_target(Vec3(target_x, 0, 0))
            self._reset_camera_to_default_view()
            self.camera_controller.enable_controls()

    def _store_original_camera_state(self):
        if not hasattr(self, 'original_camera_pos'):
            self.original_camera_pos = self.cam.getPos()
            self.original_camera_hpr = self.cam.getHpr()

    def _reset_camera_to_default_view(self):
        # Use the new reset method for cleaner code
        self.camera_controller.reset_to_default_view()

    def _restore_camera_view(self):
        if hasattr(self, 'original_camera_pos') and hasattr(self, 'original_camera_hpr'):
            self.cam.setPos(self.original_camera_pos)
            self.cam.setHpr(self.original_camera_hpr)
        
        # Reset camera target
        if hasattr(self, 'camera_controller'):
            from panda3d.core import Vec3
            self.camera_controller.set_target(Vec3(0, 0, 0))
            self.camera_controller.enable_controls()

    def _clear_favorite_objects(self):
        self._clear_favorite_objects_from_scene()
        self._restore_camera_view()

    def _clear_favorite_objects_from_scene(self):
        if hasattr(self, 'favorite_objects'):
            for obj_np in self.favorite_objects:
                obj_np.removeNode()
            self.favorite_objects = []

    def _highlight_favorite(self, favorite_index):
        if not self.favorites_list:
            return
        
        self.current_favorite_index = favorite_index
        self._focus_camera_on_current_favorite()

    # ============================================================================
    # PERFORMANCE MONITORING
    # ============================================================================

    def get_performance_stats(self) -> Dict[str, Any]:
        stats = {
            "object_creation": self.object_service.get_performance_stats(),
            "cache_performance": self.object_service.get_cache_stats(),
            "parameter_updates": {
                "pending_updates": len(self._pending_parameter_updates),
                "last_update_time": self._last_parameter_update_time
            }
        }
        return stats


# ============================================================================
# PERFORMANCE MONITORING UTILITY
# ============================================================================

class PerformanceMonitor:
    
    def __init__(self):
        self.start_time = time.time()
        self.measurements = {}
    
    def start_measurement(self, name: str):
        self.measurements[name] = time.time()
    
    def end_measurement(self, name: str) -> float:
        if name in self.measurements:
            duration = time.time() - self.measurements[name]
            del self.measurements[name]
            return duration
        return 0.0
    
    def get_uptime(self) -> float:
            
        return time.time() - self.start_time

