import os
import shutil
import shutil
import numpy as np
import pandas as pd
import json
import zipfile

class GradescopeTest:
    def __init__(self,
                 name : str,
                 max_score : int):
        self.name = name
        self.max_score = max_score
        
    def run(self, **kwargs):
        """
        Runs the test
        
        Returns:
        --------
        score : int
            The score obtained in the test
        feedback : str
            Feedback message for the test
        """
        raise NotImplementedError("Subclasses should implement this!")
    
def compute_dsq(x, a=None, b=None):
    if a is None:
        a = np.array([-10, -10, -10])
    if b is None:
        b = np.array([10, 10, 10])
    dab = np.linalg.norm(b - a)
    uab = (b - a) / dab
 
    # Compute dsq from x to line segment ab
    w = (x - a[None,:]).dot(uab)
    wclip = np.clip(w, 0, dab)
    z = a + wclip[:, None] * uab
    dsq = np.sum((z - x)**2, axis=1)

    return dsq


class TestPython(GradescopeTest):
    """
    Test the python implementation 
    """
    def __init__(
            self,
            tol : float =1e-4,
            ntest_min : int =100):
        """
        Constructor

        Parameters:
        -----------        
        tol : float
            Tolerance for zero (|f(x_root)| < tol)
        ntest_min : int
            Minimum number of test samples required in the CSV file
        """
        self.tol = tol
        self.ntest_min = ntest_min

        # Score for function value and zero tests
        max_score = 10
        super().__init__(
            name=f"Python Implementation", 
            max_score=max_score)
        
    def run(self):
        """
        Test Python implementation by reading CSV
        """
        # Construct CSV filename
        csv_file = f'data/dsq_python.csv'


        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Check if there are enough samples
            num_samples = len(df)
            if num_samples < self.ntest_min:
                score = 0
                feedback = f"Insufficient samples: {num_samples} samples found, but at least 100 required."
                return score, feedback
            
            # Extract columns
            x0 = df['x0'].values
            x1 = df['x1'].values
            x2 = df['x2'].values
            x = np.stack([x0, x1, x2], axis=1)
            dsq = df['dsq'].values

            dsq_exp = compute_dsq(x)


            # Compute MSE of fx
            mae = np.mean(np.abs(dsq - dsq_exp))

            # Feedback for the Python implementation
            feedback = "\nPython implementation test:  "
            if mae < self.tol:
                feedback += "PASS"
                score = 1
            elif mae < 10 * self.tol:
                feedback += "PARTIAL CREDIT"
                score = 0.5
            else:
                feedback += "FAIL."                
                score = 0
            feedback += "  dsq error: %12.4e tol: %12.e\n" %\
                        (mae, self.tol)
            score = int(score * self.max_score)
            return score, feedback
        
        except FileNotFoundError:
            score = 0
            feedback = f"Error: File '{csv_file}' not found."
            return score, feedback
        except Exception as e:
            score = 0
            feedback = f"Error reading or processing file: {str(e)}"
            return score, feedback


class TestVitisFunctional(GradescopeTest):
    """
    Functional test for the Vitis implementation 
    """
    def __init__(
            self,
            tol : float =1e-4,
            ntest_min : int =100):
        """
        Constructor

        Parameters:
        -----------        
        tol : float
            Tolerance for zero (|f(x_root)| < tol)
        ntest_min : int
            Minimum number of test samples required in the CSV file
        """
        self.tol = tol
        self.ntest_min = ntest_min

        # Score for function value and zero tests
        max_score = 10
        super().__init__(
            name=f"Vitis functional test", 
            max_score=max_score)
        
    def run(self):
        """
        Test Vitis functionality implementation by reading CSV
        """
        # Construct CSV filename
        csv_file = f'data/dsq_comparison.csv'


        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Check if there are enough samples
            num_samples = len(df)
            if num_samples < self.ntest_min:
                score = 0
                feedback = f"Insufficient samples: {num_samples} samples found, but at least 100 required."
                return score, feedback
            
            # Extract columns
            x0 = df['x0'].values
            x1 = df['x1'].values
            x2 = df['x2'].values
            x = np.stack([x0, x1, x2], axis=1)
            dsq = df['dsq'].values
            dsq_dut = df['dsq_dut'].values 

            # Compute MSE of fx
            mae = np.mean(np.abs(dsq - dsq_dut))


            # Feedback for function value test
            feedback = "\nVitis functional test:  "
            if mae < self.tol:
                feedback += "PASS"
                score = 1
            elif mae < 10 * self.tol:
                feedback += "PARTIAL CREDIT"
                score = 0.5
            else:
                feedback += "FAIL."                
                score = 0
            feedback += "  dsq error: %12.4e tol: %12.e\n" %\
                        (mae, self.tol)
            score = int(score * self.max_score)
            return score, feedback
        
        except FileNotFoundError:
            score = 0
            feedback = f"Error: File '{csv_file}' not found."
            return score, feedback
        except Exception as e:
            score = 0
            feedback = f"Error reading or processing file: {str(e)}"
            return score, feedback


class TestVitisPipeline(GradescopeTest):
    def __init__(
            self, 
            pipeline_ii_max : int = 1,
            pipeline_depth_max : int = 80):
        self.pipeline_ii_max = pipeline_ii_max
        self.pipeline_depth_max = pipeline_depth_max
        max_score = 10
        super().__init__(
            name=f"Vitis pipeline test", 
            max_score=max_score)
        
    def run(self):
        csv_file = f'data/csynth_loop_info.csv'

        try:
            df = pd.read_csv(csv_file)
        except FileNotFoundError:
            return 0, f"Error: File '{csv_file}' not found."
        except Exception as exc:
            return 0, f"Error reading file '{csv_file}': {str(exc)}"

        required_columns = ['PipelineII', 'PipelineDepth']
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            missing_list = ', '.join(missing_columns)
            return 0, (
                f"Error: Missing required column(s) in '{csv_file}': {missing_list}."
            )

        name_column = df.columns[0]
        if name_column not in df.columns:
            return 0, f"Error: Missing loop-name column in '{csv_file}'."

        loop_rows = df[df[name_column].astype(str).str.contains('compute_loop', na=False)]
        if loop_rows.empty:
            return 0, (
                f"Error: No row containing 'compute_loop' found in '{csv_file}'."
            )

        loop_row = loop_rows.iloc[0]

        try:
            pipeline_ii = int(float(loop_row['PipelineII']))
            pipeline_depth = int(float(loop_row['PipelineDepth']))
        except KeyError as exc:
            return 0, f"Error: Missing required column in '{csv_file}': {str(exc)}"
        except (TypeError, ValueError):
            return 0, (
                "Error: Invalid pipeline values for 'compute_loop' in "
                f"'{csv_file}'."
            )

        ii_ok = pipeline_ii <= self.pipeline_ii_max
        depth_ok = pipeline_depth <= self.pipeline_depth_max
        score = 0
        if ii_ok:
            score += 5
        if depth_ok:
            score += 5

        feedback = (
            "\nVitis pipeline test: "
            f"compute_loop PipelineII={pipeline_ii} "
            f"(max {self.pipeline_ii_max}), "
            f"PipelineDepth={pipeline_depth} "
            f"(max {self.pipeline_depth_max})."
        )

        if ii_ok and depth_ok:
            return score, feedback + " PASS\n"

        failures = []
        if not ii_ok:
            failures.append(
                f"PipelineII exceeds limit: {pipeline_ii} > {self.pipeline_ii_max}"
            )
        if not depth_ok:
            failures.append(
                f"PipelineDepth exceeds limit: {pipeline_depth} > {self.pipeline_depth_max}"
            )

        return score, feedback + " FAIL. " + '; '.join(failures) + "\n"


def submit(
    test_outputs : list,
    total_score : float,
):
    
    
    # Check if required files exist
    data_dir = os.path.join(os.getcwd(), 'data')
    plot_dir = os.path.join(os.getcwd(), 'plots')
    zip_files = [   os.path.join(os.getcwd(),'line_inter.cpp'),\
                os.path.join(os.getcwd(),'line_inter_tb.cpp'),\
                os.path.join(os.getcwd(),'line_inter.ipynb'),\
                os.path.join(data_dir, 'csynth_loop_info.csv'),\
                os.path.join(data_dir, 'csynth_resource_usage.csv'),\
                os.path.join(plot_dir, 'dsq_comparison_plot.png'),\
                os.path.join(plot_dir, 'dsq_plot.png')]
    for f in zip_files:
        if not os.path.isfile(f):
            print(f"Error: Required file {f} not found in current directory.")
            exit(1)

    # Build results in new format
    results = {
        'tests': test_outputs,
        'score': total_score
    }


    # Write results to a JSON file
    with open('submitted_results.json', 'w') as f:
        json.dump(results, f, indent=4)

    # Create submission directory
    submission_dir = 'submission'
    if os.path.exists(submission_dir):
        shutil.rmtree(submission_dir)
    os.makedirs(submission_dir)

    # Copy files to submission directory
    shutil.copy('submitted_results.json', os.path.join(submission_dir, 'submitted_results.json'))
    for f in zip_files:
        shutil.copy(f, os.path.join(submission_dir, os.path.basename(f)))

    # Create submission.zip containing the results and required source files
    with zipfile.ZipFile('submission.zip', 'w') as zipf:
        zipf.write('submitted_results.json', arcname='submitted_results.json')
        for f in zip_files:
            zipf.write(f, arcname=os.path.basename(f))

    print("Submission package created: submission.zip")
    print("Submission directory created: submission/")
    print("Upload submission.zip to Gradescope.")

def main():
    import argparse


    # List of possible tests
    tests = {
        'python': TestPython(),
        'functional': TestVitisFunctional(),
        'pipeline': TestVitisPipeline()
    }
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run tests root solve lab')
    parser.add_argument('--tests', nargs='+', default=['python'], 
                        help='List of tests to run (e.g., python, all)')
    parser.add_argument('--submit', action='store_true',
                        help='Create submission package after running tests')
    args = parser.parse_args()
    
    # Initialize list to store test outputs
    test_outputs = []
    
    # Determine which tests to run
    if 'all' in [t.lower() for t in args.tests]:
        # Run all tests
        tests_to_run = tests.keys()
    else:
        # Run only specified tests
        tests_to_run = [t.lower() for t in args.tests]

    # Loop over the list of tests
    for tname, tclass in tests.items():
        if tname.lower() in tests_to_run:
            print(f"Running test: {tname}")
            
            # Run the test with default parameters
            score, feedback = tclass.run()
            
            # Create test output dictionary
            test_out = {
                'name': tclass.name,
                'max_score': tclass.max_score,
                'score': score, 
                'feedback': feedback
            }
            
            # Add to list of test outputs
            test_outputs.append(test_out)
            
            # Print test result
            print(f"\n{tclass.name}:")
            print(f"  Score: {test_out['score']}/{tclass.max_score}")
            print(f"  Feedback: {feedback}")        
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    total_score = 0
    total_max_score = 0
    for test_out in test_outputs:
        print(f"{test_out['name']}: {test_out['score']}/{test_out['max_score']}")
        total_score += test_out['score']
        total_max_score += test_out['max_score']
    print("="*60)
    print(f"Total Score: {total_score}/{total_max_score}")
    
    # Call submit if --submit flag is set
    if args.submit:
        print("\n" + "="*60)
        print("Creating submission package...")
        print("="*60)
        submit(test_outputs, total_score)
    
    return test_outputs


if __name__ == "__main__":
    main()

