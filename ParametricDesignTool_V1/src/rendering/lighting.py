from panda3d.core import AmbientLight, DirectionalLight, Vec4


def setup_lights(render):
    """Setup ambient and directional lighting for the scene."""
    
    # Ambient light for overall illumination
    amb = AmbientLight("ambient")
    amb.setColor(Vec4(0.3, 0.3, 0.35, 1))
    amb_np = render.attachNewNode(amb)
    render.setLight(amb_np)

    # Directional light (sun) for shadows and highlights
    sun = DirectionalLight("sun")
    sun.setColor(Vec4(0.9, 0.9, 0.9, 1))
    sun_np = render.attachNewNode(sun)
    sun_np.setHpr(-30, -60, 0)
    render.setLight(sun_np)

    # Enable automatic shader generation
    render.setShaderAuto()
