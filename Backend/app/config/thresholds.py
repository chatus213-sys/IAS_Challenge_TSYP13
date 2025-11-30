# CO
CO_CEILING = 200
CO_STEL = 200
CO_TWA = 35
# CO color bands for reference/expansion (ppm)
CO_LIMITS = {
    "green": (0, 15),
    "yellow": (15, 30),
    "orange": (30, 100),
    "red": (100, 200),
    "dark-red": (200, 400),
    "purple": (400, 999999),
}

# CO₂ (ppm) — reference ranges (currently unused by processing pipeline)
CO2_LIMITS = {
    "green": (400, 800),
    "yellow": (800, 1200),
    "orange": (1200, 5000),
    "red": (5000, 10000),
    "dark-red": (10000, 30000),
    "purple": (30000, 999999),
}
# PM2.5
PM25_LIMITS = {
    "green": (0, 15),
    "yellow": (15, 30),
    "orange": (30, 60),
    "red": (60, 100),
    "dark-red": (100, 999999),
}

# PM10
PM10_LIMITS = {
    "green": (5, 40),
    "yellow": (40, 80),
    "orange": (80, 120),
    "red": (120, 150),
    "dark-red": (150, 999999),
}

# Temperature
TEMP_LIMITS = {
    "green": (-273, 22),          # Comfortable
    "yellow": (22, 26),           # Mild heat
    "orange": (26, 30),           # Heat stress begins
    "red": (30, 32),              # High heat risk
    "dark-red": (32, 35),         # Severe heat stress
    "purple": (35, 100),    
}

# Pressure
PRESSURE_LIMITS = {
    "purple-low": (0, 800),        # < 80 kPa critical
    "dark-red-low": (800, 850),    # 80–85 kPa dangerous
    "red-low": (850, 900),         # 85–90 kPa hazardous
    "orange-low": (900, 950),      # 90–95 kPa abnormal
    "yellow-low": (950, 980),      # 95–98 kPa slight deviation
    "green": (980, 1030),          # 98–102 kPa normal
    "yellow-high": (1030, 1050),   # 102–105 kPa slight deviation
    "orange-high": (1050, 1080),   # 105–108 kPa abnormal
    "red-high": (1080, 1100),      # 108–110 kPa hazardous
    "dark-red-high": (1100, 1150), # 110–115 kPa dangerous
    "purple-high": (1150, 2000),     # Overpressure risk
}

# WBGT
WBGT_THRESHOLDS = {
    "green": (0, 25),
    "yellow": (25, 28),
    "orange": (28, 31),
    "red": (31, 33),
    "dark_red": (33, 35),
    "purple": (35, 100),
}