import os
import re

LOGS_PATH = os.path.join(os.getcwd(), '/home/alexey/Documents/Work/task/logs')
B_DIFF = 0.1 # Total of bricks criteria
M_DIFF = 0.5 # Memory set peak criteria

def form_name(s : str) -> str:
    """
    used to make propper filenames
    """
    s = f'{str(s)}/{str(s)}.stdout'
    return s

def parse_memory(line : str) -> float:
    """
    finds memory set peak in line and parses it using regex
    """
    return float(re.search(r'Memory Working Set Peak = ([0-9]*\.?[0-9]*)', line).group(1))

def parse_bricks(line : str) -> int:
    """
    finds total bricks count and parses it using regex
    """
    return int(re.search(r'Total=(\d+)', line).group(1))

def read_report(report : dict, path : str) -> dict:
    """
    reads report.txt and writes to stdout
    takes report : dict, path : str
    report needed to simplify analysis and get group and case names
    """
    # if file is empty, write OK to stdout
    if os.stat(os.path.join(path, 'report.txt')).st_size == 0: 
        std_info = 'OK: '
        std_info += os.path.join(report['group'], report['case'])
        std_info += '/'
        print(std_info)
    else:
        std_info = 'FAIL: '
        std_info += os.path.join(report['group'], report['case'])
        std_info += '/'
        print(std_info)
        with open(os.path.join(path, 'report.txt'), 'r') as f:
            print(f.read(), end='')

def make_report(results : dict, path : str):
    """
    makes report.txt file in path directory
    takes results : dict , path : str
    """
    with open(os.path.join(path, 'report.txt'), 'w') as f:
        # checking ft_run and ft_ref if missing write to report and return
        if not results['ft_run'] or  not results['ft_reference']:
            if not results['ft_run']:
                print("directory missing: ft_run", file=f)
            if not results['ft_reference']:
                print("directory missing: ft_reference", file=f)
            f.close()
            return

        # checking missing and extra files if found -> return
        if results['missing_files'] != [] or results['extra_files'] != []:
            if results['missing_files'] != []:
                missing = ', '.join(results['missing_files'])
                print(f"In ft_run there are missing files present in ft_reference: {missing}", file=f)
            if results['extra_files'] != []:
                extra = ', '.join(results['extra_files'])
                print(f"In ft_run there are extra files not present in ft_reference: {extra}", file=f)
            f.close()
            return

        reps = [] # to store errors in report, needed to sort errors

        cases_tests = results['cases_errors']
        if any(cases_tests.values()):
            for test in cases_tests:
                if cases_tests[test] != []:
                    for error in cases_tests[test]:
                        num = error[0]
                        line = error[1]
                        reps.append(f"{test}/{test}.stdout({num}): {line}")

        solver_tests = results['solver']
        if any(solver_tests.values()):
            for test in solver_tests:
                if solver_tests[test]:
                    reps.append(f"{test}/{test}.stdout: missing 'Solver finished at'")

        memory = results['memory_test']
        for test in memory:
            run = memory[test][0]
            ref = memory[test][1]
            diff = (run - ref) / ref
            if abs(diff) > M_DIFF:
                rep = f"{test}/{test}.stdout: different 'Memory Working Set Peak' "
                stats = f"(ft_run={run}, ft_reference={ref}, rel.diff={diff:.2f}, criterion={M_DIFF:.1f})"
                reps.append(rep+stats)

        bricks = results['bricks']
        for test in bricks:
            run = bricks[test][0]
            ref = bricks[test][1]
            diff = round((run - ref) / ref, 2)
            if abs(diff) > B_DIFF:
                rep = f"{test}/{test}.stdout: different 'Total' of bricks "
                stats = f"(ft_run={run}, ft_reference={ref}, rel.diff={diff:.2f}, criterion={B_DIFF:.1f})"
                reps.append(rep+stats)

        reps.sort() # for appropriate order of errors
        for report in reps:
            print(report, file=f)

def check_test(test_path : str) -> dict:
    """
    check test in test_path
    """
    report = {
        'group': os.path.split(os.path.split(test_path)[0])[-1],
        'case': os.path.split(test_path)[-1],
        'ft_run': 1 if os.path.exists(os.path.join(test_path, 'ft_run')) else 0,
        'ft_reference': 1 if os.path.exists(os.path.join(test_path, 'ft_reference')) else 0
    }

    # if there are no ft_ref or ft_run, stop checking continue to report
    if not report['ft_reference'] or not report['ft_run']:
        return report

    # getting paths to folders with .stdout files
    ft_run = os.listdir(os.path.join(test_path, 'ft_run'))
    ft_ref = os.listdir(os.path.join(test_path, 'ft_reference'))
    ft_run = set(map(int, ft_run))
    ft_ref = set(map(int, ft_ref))
    report['missing_files'] = list(map(lambda x: f"'{form_name(x)}'", ft_ref - ft_run))
    report['extra_files'] = list(map(lambda x: f"'{form_name(x)}'", ft_run - ft_ref))

    # if there are extra or missing, stop checking continue to report
    if report['missing_files'] != [] or report['extra_files'] != []:
        return report

    errors = {} # to store line num and line of cases
    solver_exist = {} # to store solver existance of solver lines
    memory_peak = {} # to store case : last memory peak
    bricks = {} # to store case : last bricks number
    for case in ft_run:
        errors[case] = []
        solver_exist[case] = True
        # search ft_run file
        with open(os.path.join(test_path,'ft_run', form_name(case)), 'r') as f:
            num = 1
            for line in f:
                if ' error' in line.lower() or '\terror' in line.lower():
                    errors[case].append((num, line.strip('\n')))
                elif line.startswith('Solver finished at'):
                    solver_exist[case] = False
                elif line.startswith('Memory Working Set Current'):
                    run_peaks = parse_memory(line)
                elif line.startswith('MESH::Bricks: Total='):
                    run_bricks = parse_bricks(line)
                num += 1

        with open(os.path.join(test_path, 'ft_reference', form_name(case)), 'r') as f:
            for line in f: # search file for errors
                if line.startswith('Memory Working Set Current'):
                    ref_peaks = parse_memory(line)
                elif line.startswith('MESH::Bricks: Total='):
                    ref_bricks = parse_bricks(line)

        memory_peak[case] = (run_peaks, ref_peaks)
        bricks[case] = (run_bricks, ref_bricks)

    # linking results to report
    report['solver'] = solver_exist
    report['cases_errors'] = errors
    report['memory_test'] = memory_peak
    report['bricks'] = bricks
    return report

# getting list with absolute path to test groups
folders = list(map(lambda x: os.path.join(LOGS_PATH, x), sorted(os.listdir(LOGS_PATH))))

for group in folders:
    tests = list(map(lambda x: os.path.join(LOGS_PATH, group, x), sorted(os.listdir(group))))
    for test in tests:
        report = check_test(test)
        make_report(report, test) # make report
        read_report(report, test) # read it to stdout

