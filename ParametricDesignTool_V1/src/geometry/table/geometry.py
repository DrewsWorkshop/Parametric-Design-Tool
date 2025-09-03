from panda3d.core import Geom, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter



def tableGeometry(segment_count=16, object_width=1.0, twist_angle=0.0, 
                           twist_groove_depth=1.0, vertical_wave_freq=3.0, 
                           vertical_wave_depth=1.0) -> Geom:

    import math

    ObjectType = "Table"

    radius=1.0
    height=2.0
    segments=100
    height_segments=50
    
    vformat = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("cylinder_modulated_vn", vformat, Geom.UHStatic)

    vwriter = GeomVertexWriter(vdata, "vertex")
    nwriter = GeomVertexWriter(vdata, "normal")

    indices = []
    half_height = height / 2.0

    def add_vertex(x, y, z, nx, ny, nz):
        """Helper to add a vertex with its normal."""
        vwriter.addData3f(x, y, z)
        nwriter.addData3f(nx, ny, nz)
        return vwriter.getWriteRow() - 1

    def get_surface_modulation(phi, length_ratio):
        """Surface modulation function converted from C#."""
        phi += twist_angle * 0.067 * math.pi * length_ratio
        modulated_radius = object_width + (twist_groove_depth * 0.06) * math.cos(segment_count * phi) + (vertical_wave_depth * 0.15) * math.cos(vertical_wave_freq * length_ratio)
        return modulated_radius

    # Generate vertices for top and bottom faces (using modulated radius)
    top_center = add_vertex(0, 0, half_height, 0, 0, 1)
    bottom_center = add_vertex(0, 0, -half_height, 0, 0, -1)
    
    # Generate vertices around the circumference for top and bottom
    top_vertices = []
    bottom_vertices = []
    
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        
        # Get modulated radius for top and bottom
        top_radius = get_surface_modulation(angle, 1.0)  # Top face
        bottom_radius = get_surface_modulation(angle, 0.0)  # Bottom face
        
        # Top face vertices
        top_v = add_vertex(top_radius * math.cos(angle), top_radius * math.sin(angle), half_height, 0, 0, 1)
        top_vertices.append(top_v)
        
        # Bottom face vertices  
        bottom_v = add_vertex(bottom_radius * math.cos(angle), bottom_radius * math.sin(angle), -half_height, 0, 0, -1)
        bottom_vertices.append(bottom_v)
    
    # Create top face triangles (fan)
    for i in range(segments):
        next_i = (i + 1) % segments
        indices.extend([
            (top_center, top_vertices[i], top_vertices[next_i])
        ])
    
    # Create bottom face triangles (fan)
    for i in range(segments):
        next_i = (i + 1) % segments
        indices.extend([
            (bottom_center, bottom_vertices[next_i], bottom_vertices[i])
        ])
    
    # Create side wall with height segments
    for h in range(height_segments):
        z1 = half_height - (height * h) / height_segments
        z2 = half_height - (height * (h + 1)) / height_segments
        length_ratio1 = 1.0 - (h / height_segments)
        length_ratio2 = 1.0 - ((h + 1) / height_segments)
        
        for i in range(segments):
            next_i = (i + 1) % segments
            
            angle1 = (2.0 * math.pi * i) / segments
            angle2 = (2.0 * math.pi * next_i) / segments
            
            # Get modulated radii for this height level
            radius1_lower = get_surface_modulation(angle1, length_ratio2)
            radius1_upper = get_surface_modulation(angle1, length_ratio1)
            radius2_lower = get_surface_modulation(angle2, length_ratio2)
            radius2_upper = get_surface_modulation(angle2, length_ratio1)
            
            # Calculate approximate normals (simplified)
            mid_angle = (angle1 + angle2) / 2.0
            nx = math.cos(mid_angle)
            ny = math.sin(mid_angle)
            
            # Add vertices for this quad
            v1 = add_vertex(radius1_upper * math.cos(angle1), radius1_upper * math.sin(angle1), z1, nx, ny, 0)
            v2 = add_vertex(radius1_lower * math.cos(angle1), radius1_lower * math.sin(angle1), z2, nx, ny, 0)
            v3 = add_vertex(radius2_lower * math.cos(angle2), radius2_lower * math.sin(angle2), z2, nx, ny, 0)
            v4 = add_vertex(radius2_upper * math.cos(angle2), radius2_upper * math.sin(angle2), z1, nx, ny, 0)
            
            # Create two triangles for the quad
            indices.extend([
                (v1, v2, v3),
                (v1, v3, v4)
            ])

    tris = GeomTriangles(Geom.UHStatic)
    for a, b, c in indices:
        tris.addVertices(a, b, c)
        tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    return ObjectType,geom