import os
import re

LOGS_PATH = os.path.join(os.getcwd(), '/home/alexey/Documents/Work/task/logs')

def make_report(results, path):
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
            if abs(diff) > 0.5:
                rep = f"{test}/{test}.stdout: different 'Memory Working Set Peak' "
                stats = f"(ft_run={run}, ft_reference={ref}, rel.diff={diff:.2f}, criterion=0.5)"
                reps.append(rep+stats)

        bricks = results['bricks']
        for test in bricks:
            run = bricks[test][0]
            ref = bricks[test][1]
            diff = round((run - ref) / ref, 2)
            if abs(diff) > 0.1:
                rep = f"{test}/{test}.stdout: different 'Total' of bricks "
                stats = f"(ft_run={run}, ft_reference={ref}, rel.diff={diff:.2f}, criterion=0.1)"
                reps.append(rep+stats)

        reps.sort() # for appropriate order of errors
        for report in reps:
            print(report, file=f)

def read_report(report, path):
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
            print(f.read().strip('\n'))

# getting list with absolute path to test groups
folders = list(map(lambda x: os.path.join(LOGS_PATH, x), sorted(os.listdir(LOGS_PATH))))

for group in folders:
    tests = list(map(lambda x: os.path.join(LOGS_PATH, group, x), sorted(os.listdir(group))))
    for test in tests:
        report = {
            'group': os.path.split(os.path.split(test)[0])[-1],
            'case': os.path.split(test)[-1],
            'ft_run': 1 if os.path.exists(os.path.join(test, 'ft_run')) else 0,
            'ft_reference': 1 if os.path.exists(os.path.join(test, 'ft_reference')) else 0
        }

        # if there are no ft_ref or ft_run, stop checking continue to report
        if not report['ft_reference'] or not report['ft_run']:
            make_report(report, test)
            read_report(report, test)
            continue
        
        # getting paths to folders with .stdout files
        ft_run = os.listdir(os.path.join(test, 'ft_run'))
        ft_ref = os.listdir(os.path.join(test, 'ft_reference'))
        ft_run = set(map(int, ft_run))
        ft_ref = set(map(int, ft_ref))
        report['missing_files'] = list(map(lambda x: f"'{str(x)}/{str(x)}.stdout'", ft_ref - ft_run))
        report['extra_files'] = list(map(lambda x: f"'{str(x)}/{str(x)}.stdout'", ft_run - ft_ref))
        
        # if there are extra or missing, stop checking continue to report
        if report['missing_files'] != [] or report['extra_files'] != []:
            make_report(report, test)
            read_report(report, test)
            continue

        errors = {} # to store line num and line of cases
        solver_exist = {} # to store solver existance of solver lines
        memory_peak = {} # to store case : last memory peak
        bricks = {} # to store case : last bricks number
        for case in ft_run:
            # read content of .stdout files
            with open(os.path.join(test,'ft_run', f'{str(case)}/{str(case)}.stdout'), 'r') as f:
                run_text = f.readlines()
            with open(os.path.join(test, 'ft_reference', f'{str(case)}/{str(case)}.stdout'), 'r') as f:
                ref_text = f.readlines()
            errors[case] = []
            solver_exist[case] = True
            run_peaks = []
            ref_peaks = []
            for num, line in enumerate(run_text, start=1): # search file for errors
                if ' error' in line.lower() or '\terror' in line.lower():
                    errors[case].append((num, run_text[num - 1].strip('\n')))
                if line.startswith('Solver finished at'):
                    solver_exist[case] = False
                if line.startswith('Memory Working Set Current'):
                    run_peaks.append(float(line.split()[-2]))
                if line.startswith('MESH::Bricks: Total='):
                    run_bricks = int(re.search(r'Total=\d+', line).group().split('=')[-1])
            
            for line in ref_text: # search file for errors
                if line.startswith('Memory Working Set Current'):
                    ref_peaks.append(float(line.split()[-2]))
                if line.startswith('MESH::Bricks: Total='):
                    ref_bricks = int(re.search(r'Total=\d+', line).group().split('=')[-1])

            memory_peak[case] = (run_peaks[-1], ref_peaks[-1])
            bricks[case] = (run_bricks, ref_bricks)

        # linking results to report
        report['solver'] = solver_exist
        report['cases_errors'] = errors
        report['memory_test'] = memory_peak
        report['bricks'] = bricks
        make_report(report, test) # make report
        read_report(report, test) # read it to stdout
