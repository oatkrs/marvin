import yaml
import os
from typing import Dict, Any

class ConfigError(Exception):
    pass

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate the YAML configuration file.
    """
    if not os.path.exists(config_path):
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML configuration: {e}")

    if not config:
        raise ConfigError("Configuration file is empty")

    # Basic validation
    if 'sources' not in config:
        raise ConfigError("Configuration missing 'sources' section")
    if 'sinks' not in config:
        raise ConfigError("Configuration missing 'sinks' section")

    return config
