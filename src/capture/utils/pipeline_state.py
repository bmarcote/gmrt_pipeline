"""Pipeline state management for CAPTURE."""

import os
import json
import logging
from datetime import datetime


class PipelineState:
    """Manages pipeline execution state and tracks completed steps."""
    
    def __init__(self, state_file='.capture_state.json'):
        """Initialize pipeline state."""
        self.state_file = state_file
        self.state = self.load_state()
    
    def load_state(self):
        """Load pipeline state from file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load state file: {e}")
                return {}
        return {}
    
    def save_state(self):
        """Save pipeline state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save state file: {e}")
    
    def check_step_needed(self, step_name, inputs, outputs):
        """
        Check if a step needs to be run based on input/output file timestamps.
        
        Args:
            step_name: Name of the pipeline step
            inputs: List of input file paths
            outputs: List of output file paths
            
        Returns:
            True if step needs to be run, False otherwise
        """
        # If any output is missing, step needs to be run
        for output in outputs:
            if not os.path.exists(output):
                logging.debug(f"Output {output} missing for step {step_name}")
                return True
        
        # Check if inputs are newer than outputs
        input_times = []
        for inp in inputs:
            if os.path.exists(inp):
                input_times.append(os.path.getmtime(inp))
        
        output_times = []
        for out in outputs:
            if os.path.exists(out):
                output_times.append(os.path.getmtime(out))
        
        # If any input is newer than any output, step needs to be run
        if input_times and output_times:
            newest_input = max(input_times)
            oldest_output = min(output_times)
            if newest_input > oldest_output:
                logging.debug(f"Inputs newer than outputs for step {step_name}")
                return True
        
        logging.debug(f"Step {step_name} outputs are up to date")
        return False
    
    def mark_step_complete(self, step_name, outputs):
        """
        Mark a step as complete in the state.
        
        Args:
            step_name: Name of the pipeline step
            outputs: List of output file paths
        """
        self.state[step_name] = {
            'completed': True,
            'timestamp': datetime.now().isoformat(),
            'outputs': outputs
        }
        self.save_state()
        logging.debug(f"Marked step {step_name} as complete")
    
    def is_step_complete(self, step_name):
        """Check if a step has been marked as complete."""
        return self.state.get(step_name, {}).get('completed', False)
    
    def clear_step(self, step_name):
        """Clear completion status for a step."""
        if step_name in self.state:
            del self.state[step_name]
            self.save_state()
            logging.debug(f"Cleared step {step_name} from state")
    
    def reset(self):
        """Reset all pipeline state."""
        self.state = {}
        self.save_state()
        logging.info("Pipeline state reset")
