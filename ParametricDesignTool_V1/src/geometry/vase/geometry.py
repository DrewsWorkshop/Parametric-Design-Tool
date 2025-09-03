from panda3d.core import Geom, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter



def vaseGeometry(segment_count=16, object_width=1.0, twist_angle=0.0, 
                           twist_groove_depth=1.0, vertical_wave_freq=3.0, 
                           vertical_wave_depth=1.0, wall_thickness=0.5) -> Geom:

    import math

    ObjectType = "Vase"

    radius=1.0
    height=7.0 #unitless, but this is so called inches
    segments=40
    height_segments=40
    
    vformat = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("pipe_modulated_vn", vformat, Geom.UHStatic)

    vwriter = GeomVertexWriter(vdata, "vertex")
    nwriter = GeomVertexWriter(vdata, "normal")

    indices = []
    half_height = height / 2.0
    
    # Track bounding box as we create vertices
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    min_z, max_z = float('inf'), float('-inf')
    
    def add_vertex(x, y, z, nx, ny, nz):
        """Helper to add a vertex with its normal and track bounding box."""
        nonlocal min_x, max_x, min_y, max_y, min_z, max_z
        
        # Update bounding box
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
        min_z, max_z = min(min_z, z), max(max_z, z)
        
        vwriter.addData3f(x, y, z)
        nwriter.addData3f(nx, ny, nz)
        return vwriter.getWriteRow() - 1

    def get_surface_modulation(phi, length_ratio):
        phi += twist_angle * 0.067 * math.pi * length_ratio
        modulated_radius = object_width + (twist_groove_depth * 0.06) * math.cos(segment_count * phi) + (vertical_wave_depth * 0.15) * math.cos(vertical_wave_freq * length_ratio)
        return modulated_radius

    def get_inner_surface_modulation(phi, length_ratio):
        phi += twist_angle * 0.067 * math.pi * length_ratio
        modulated_radius = (object_width - wall_thickness) + (twist_groove_depth * 0.06) * math.cos(segment_count * phi) + (vertical_wave_depth * 0.15) * math.cos(vertical_wave_freq * length_ratio)
        return modulated_radius

    # Generate vertices for top and bottom faces (using modulated radius)
    # Top face - outer ring
    top_outer_vertices = []
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        top_radius = get_surface_modulation(angle, 1.0)  # Top face
        top_v = add_vertex(top_radius * math.cos(angle), top_radius * math.sin(angle), half_height, 0, 0, 1)
        top_outer_vertices.append(top_v)
    
    # Top face - inner ring
    top_inner_vertices = []
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        top_inner_radius = get_inner_surface_modulation(angle, 1.0)  # Top face
        top_v = add_vertex(top_inner_radius * math.cos(angle), top_inner_radius * math.sin(angle), half_height, 0, 0, 1)
        top_inner_vertices.append(top_v)
    
    # Bottom face - outer ring
    bottom_outer_vertices = []
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        bottom_radius = get_surface_modulation(angle, 0.0)  # Bottom face
        bottom_v = add_vertex(bottom_radius * math.cos(angle), bottom_radius * math.sin(angle), -half_height, 0, 0, -1)
        bottom_outer_vertices.append(bottom_v)
    
    # Bottom face - inner ring
    bottom_inner_vertices = []
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        bottom_inner_radius = get_inner_surface_modulation(angle, 0.0)  # Bottom face
        bottom_v = add_vertex(bottom_inner_radius * math.cos(angle), bottom_inner_radius * math.sin(angle), -half_height, 0, 0, -1)
        bottom_inner_vertices.append(bottom_v)
    
    # Create top face triangles (connecting outer and inner rings)
    for i in range(segments):
        next_i = (i + 1) % segments
        # Create quad between outer and inner rings
        indices.extend([
            (top_outer_vertices[i], top_inner_vertices[i], top_inner_vertices[next_i]),
            (top_outer_vertices[i], top_inner_vertices[next_i], top_outer_vertices[next_i])
        ])
    
    # Create bottom face triangles (connecting outer and inner rings)
    for i in range(segments):
        next_i = (i + 1) % segments
        # Create quad between outer and inner rings
        indices.extend([
            (bottom_outer_vertices[i], bottom_inner_vertices[next_i], bottom_inner_vertices[i]),
            (bottom_outer_vertices[i], bottom_outer_vertices[next_i], bottom_inner_vertices[next_i])
        ])
    
    # Create side walls with height segments
    for h in range(height_segments):
        z1 = half_height - (height * h) / height_segments
        z2 = half_height - (height * (h + 1)) / height_segments
        length_ratio1 = 1.0 - (h / height_segments)
        length_ratio2 = 1.0 - ((h + 1) / height_segments)
        
        # Store vertices for this height level
        outer_upper_vertices = []
        outer_lower_vertices = []
        inner_upper_vertices = []
        inner_lower_vertices = []
        
        for i in range(segments):
            angle = (2.0 * math.pi * i) / segments
            
            # Get modulated radii for outer surface
            outer_radius_upper = get_surface_modulation(angle, length_ratio1)
            outer_radius_lower = get_surface_modulation(angle, length_ratio2)
            
            # Get modulated radii for inner surface
            inner_radius_upper = get_inner_surface_modulation(angle, length_ratio1)
            inner_radius_lower = get_inner_surface_modulation(angle, length_ratio2)
            
            # Calculate approximate normals
            nx = math.cos(angle)
            ny = math.sin(angle)
            
            # Add outer surface vertices
            outer_upper_v = add_vertex(outer_radius_upper * math.cos(angle), outer_radius_upper * math.sin(angle), z1, nx, ny, 0)
            outer_lower_v = add_vertex(outer_radius_lower * math.cos(angle), outer_radius_lower * math.sin(angle), z2, nx, ny, 0)
            outer_upper_vertices.append(outer_upper_v)
            outer_lower_vertices.append(outer_lower_v)
            
            # Add inner surface vertices (inverted normals)
            inner_upper_v = add_vertex(inner_radius_upper * math.cos(angle), inner_radius_upper * math.sin(angle), z1, -nx, -ny, 0)
            inner_lower_v = add_vertex(inner_radius_lower * math.cos(angle), inner_radius_lower * math.sin(angle), z2, -nx, -ny, 0)
            inner_upper_vertices.append(inner_upper_v)
            inner_lower_vertices.append(inner_lower_v)
        
        # Create outer surface quads
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.extend([
                (outer_upper_vertices[i], outer_lower_vertices[i], outer_lower_vertices[next_i]),
                (outer_upper_vertices[i], outer_lower_vertices[next_i], outer_upper_vertices[next_i])
            ])
        
        # Create inner surface quads
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.extend([
                (inner_upper_vertices[i], inner_upper_vertices[next_i], inner_lower_vertices[i]),
                (inner_lower_vertices[i], inner_upper_vertices[next_i], inner_lower_vertices[next_i])
            ])
        
        # Create wall faces connecting inner and outer surfaces
        for i in range(segments):
            next_i = (i + 1) % segments
            
            # Calculate wall normal (pointing outward from inner to outer)
            angle = (2.0 * math.pi * i) / segments
            wall_nx = math.cos(angle)
            wall_ny = math.sin(angle)
            
            # Upper wall face
            indices.extend([
                (outer_upper_vertices[i], outer_upper_vertices[next_i], inner_upper_vertices[i]),
                (inner_upper_vertices[i], outer_upper_vertices[next_i], inner_upper_vertices[next_i])
            ])
            
            # Lower wall face
            indices.extend([
                (outer_lower_vertices[i], inner_lower_vertices[i], outer_lower_vertices[next_i]),
                (inner_lower_vertices[i], inner_lower_vertices[next_i], outer_lower_vertices[next_i])
            ])

    tris = GeomTriangles(Geom.UHStatic)
    for a, b, c in indices:
        tris.addVertices(a, b, c)
        tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    
    # Calculate bounding box from tracked values
    diameter = max_x - min_x
    #depth = max_y - min_y
    height_actual = max_z - min_z
    
    print(f"Vase bounding box: diameter={diameter:.2f}, height={height_actual:.2f}")
    
    return ObjectType, geom, height, diameter

