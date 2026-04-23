def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    
    # The original tile size in your spritesheet is 32x32
    native_size = 32 
    surface = pygame.Surface((native_size, native_size), pygame.SRCALPHA, 32)
    
    # Grab the specific grass tile (96, 0 is the standard for this asset pack)
    rect = pygame.Rect(96, 0, native_size, native_size)
    surface.blit(image, (0, 0), rect)
    
    # Scale the 32x32 tile up to your desired 'size'
    return pygame.transform.scale(surface, (size, size))