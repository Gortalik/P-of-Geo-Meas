#!/usr/bin/env python3
import sys
from pathlib import Path

# Set up the path correctly
geo_path = Path(__file__).parent / "GeoAdjustPro" / "src"
sys.path.insert(0, str(geo_path))

# Import after setting the path
from geoadjust.io.formats.gsi import GSIParser

def debug_height_diff(file_path):
    print(f"Checking for height difference observations in {file_path}")
    parser = GSIParser()
    result = parser.parse(Path(file_path))
    
    # Filter for height_diff observations
    height_obs = [obs for obs in result['observations'] if obs.obs_type == 'height_diff']
    
    print(f"Found {len(height_obs)} height difference observations")
    
    if height_obs:
        print("First 5 height difference observations:")
        for i, obs in enumerate(height_obs[:5]):
            print(f"  {i+1}: {obs.obs_type} from {obs.from_point} to {obs.to_point} = {obs.value}")
            print(f"       Station session: {obs.station_session_id}")
            if hasattr(obs, 'instrument_height'):
                print(f"       Instrument height: {obs.instrument_height}")
            if hasattr(obs, 'target_height'):
                print(f"       Target height: {obs.target_height}")
    else:
        print("No height difference observations found!")
        
        # Let's also check for other observation types
        obs_types = {}
        for obs in result['observations']:
            obs_type = obs.obs_type
            obs_types[obs_type] = obs_types.get(obs_type, 0) + 1
        
        print("\nAll observation types found:")
        for obs_type, count in sorted(obs_types.items()):
            print(f"  {obs_type}: {count}")

if __name__ == "__main__":
    # Test with one of the GSI files
    test_file = "test_real_mes/s5/niv/MIR0212.GSI"
    debug_height_diff(test_file)