import subprocess
import re
import numpy as np
import pandas as pd

def run_mlc():
    """Run the MLC command and parse the latency matrix."""
    try:
        # Execute the MLC command
        result = subprocess.run(["/home/date/tools/mlc/Linux/mlc", "--latency_matrix"], capture_output=True, text=True, check=True)
        output = result.stdout
        
        # Parse the latency matrix
        # Example pattern to match the matrix output
        matrix = []
        for line in output.splitlines():
            match = re.match(r"^\s*\d+\s+([\d.]+)\s+([\d.]+)", line)
            if match:
                matrix.append([float(match.group(1)), float(match.group(2))])
        return matrix
    except subprocess.CalledProcessError as e:
        print(f"Error running MLC: {e}")
        return None

def collect_and_analyze():
    """Collect data from 10 runs and analyze the latency patterns."""
    data = []
    
    for i in range(100):
        print(f"Running MLC iteration {i+1}/10...")
        matrix = run_mlc()
        print(matrix)
        if matrix:
            data.append(matrix)
        else:
            print(f"Skipping iteration {i+1} due to an error.")
    
    if not data:
        print("No data collected. Exiting.")
        return
    
    # Convert to a numpy array for analysis
    data_array = np.array(data)
    mean_results = np.mean(data_array, axis=0)
    variance_results = np.var(data_array, axis=0)
    
    # Compile results into a DataFrame
    patterns = ["0->0", "0->1", "1->0", "1->1"]
    mean_flat = mean_results.flatten()
    variance_flat = variance_results.flatten()
    
    results = pd.DataFrame({
        "Access Pattern": patterns,
        "Mean (ns)": mean_flat,
        "Variance (ns^2)": variance_flat
    })
    
    print("Analysis complete. Here are the results:")
    print(results)

# Run the analysis
if __name__ == "__main__":
    collect_and_analyze()
