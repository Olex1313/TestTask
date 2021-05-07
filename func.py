from config import LOGS_PATH, T_REF, T_RUN
import os
import re


def file_is_empty(path):
    return os.stat(path).st_size == 0

def parse_memory(s):
    return float(s.split()[-2])

def parse_bricks(s):
    return int(re.findall(r'MESH::Bricks: Total=\d+', s)[0].split('=')[-1])

def get_folders_list(cwd):
    os.chdir(cwd)
    folders = list(map(os.path.abspath, os.listdir()))
    return folders

def go_to_directory(LOGS_PATH):
    os.chdir(LOGS_PATH)
    folders = list(map(os.path.abspath, os.listdir()))
    return folders
    
def check_test_exists():
    missing = []
    cases = os.listdir()
    report = {
        'group': os.path.split(os.path.split(os.getcwd())[0])[-1],
        'case': os.path.split(os.getcwd())[-1],
        T_RUN: 1,
        T_REF: 1
    }
    if not cases:
        report[T_RUN] = 0
        report[T_REF] = 0
        return report
    else:
        if T_RUN not in cases:
            report[T_RUN] = 0
        if T_REF not in cases:
            report[T_REF] = 0
    return report
    


def check_test_missing():
    homepath = os.getcwd()
    ft_run = os.listdir(os.path.join(homepath, T_RUN))
    ft_ref = os.listdir(os.path.join(homepath, T_REF))
    ft_run = set(map(int, ft_run))
    ft_ref = set(map(int, ft_ref))
    tests_run_missing = list(map(lambda x: f'{str(x)}/{str(x)}.stdout', ft_ref - ft_run))
    tests_run_extra = list(map(lambda x: f'{str(x)}/{str(x)}.stdout', ft_run - ft_ref))
    return tests_run_missing, tests_run_extra

def check_test_errors():
    homepath = os.getcwd()
    ft_run = os.path.join(homepath, T_RUN)
    tests = os.listdir(ft_run)
    errors = {}
    for test in tests:
        errors[test] = []
        with open(os.path.join(ft_run, test, f'{test}.stdout'), 'r') as f:
            text = f.readlines()
            content = list(map(lambda x: x.lower(), text))
            for num, line in enumerate(content, start=1):
                if 'error' in line:
                    errors[test].append((num, text[num - 1].strip('\n')))
    
    return errors
                
            

def check_test_solver():
    homepath = os.getcwd()
    ft_run = os.path.join(homepath, T_RUN)
    tests = os.listdir(ft_run)
    solver_exist = {}
    for test in tests:
        with open(os.path.join(ft_run, test, f'{test}.stdout'), 'r') as f:
            content = f.read()
            if 'Solver finished at' in content:
                solver_exist[test] = False
            else:
                solver_exist[test] = True

    return solver_exist

def check_test_memory(): # -> dict: key=test, el[0] = run, el[1] = ref
    homepath = os.getcwd()
    ft_run = os.path.join(homepath, T_RUN)
    ft_ref = os.path.join(homepath, T_REF)
    tests = os.listdir(ft_run)
    memory_peak = {}
    for test in tests:
        run_peaks = []
        ref_peaks = []
        with open(os.path.join(ft_run, test, f'{test}.stdout'), 'r') as f:
            content = f.readlines()
            for line in content:
                if line.startswith('Memory Working Set Current'):
                    run_peaks.append(parse_memory(line))
        with open(os.path.join(ft_ref, test, f'{test}.stdout'), 'r') as f:
            content = f.readlines()
            for line in content:
                if line.startswith('Memory Working Set Current'):
                    ref_peaks.append(parse_memory(line))
        memory_peak[test] = (max(run_peaks), max(ref_peaks))

    return memory_peak 
    

def check_test_bricks():
    homepath = os.getcwd()
    ft_run = os.path.join(homepath, T_RUN)
    ft_ref = os.path.join(homepath, T_REF)
    tests = os.listdir(ft_run)
    bricks = {}
    for test in tests:
        with open(os.path.join(ft_run, test, f'{test}.stdout'), 'r') as f:
            run_bricks = parse_bricks(f.read())
        with open(os.path.join(ft_ref, test, f'{test}.stdout'), 'r') as f:
            ref_bricks = parse_bricks(f.read())
        bricks[test] = (run_bricks, ref_bricks)
    
    return bricks 

def memory_diff(memory_test):
    for test in memory_test:
        run = memory_test[test][0]
        ref = memory_test[test][1]
        diff = (run - ref)/ref

def make_report(results):
    with open('report.txt', 'w') as f:

        if results[T_RUN] != 1 or results[T_REF] != 1:
            if results[T_RUN] != 1:
                print('directory missing: ft_run', file=f)
            if results[T_REF] != 1:
                print('directory missing: ft_reference', file=f)
            f.close()
            return

        if results['missing_files'] != [] or results['extra_files'] != []:
            if results['missing_files'] != []:
                missing = ', '.join(results['missing_files'])
                print(f'In ft_run there are missing files present in ft_reference: {missing}', file=f)
            if results['extra_files'] != []:
                extra = ', '.join(results['extra_files'])
                print(f'In ft_run there are extra files not present in ft_reference: {extra}', file=f)
            f.close()
            return
        
        cases_tests = results['cases_errors']
        if any(cases_tests.values()):
            for test in cases_tests:
                if cases_tests[test] != []:
                    for error in cases_tests[test]:
                        num = error[0]
                        line = error[1]
                        print(f"{test}/{test}.stdout({num}): {line}", file=f)
        
        solver_tests = results['solver']
        if any(list(solver_tests.values())):
            for test in solver_tests:
                if solver_tests[test]:
                    print(f"{test}/{test}.stdout: Missing 'Solver finished at'", file=f)
        
        memory = results['memory_test']
        for test in memory:
            run = memory[test][0]
            ref = memory[test][1]
            diff = round((run - ref) / ref, 2)
            if abs(diff) > 0.5:
                rep = f"{test}/{test}.stdout: different 'Memory Working Set Peak' "
                stats = f"(ft_run={run}, ft_reference={ref}, rel.diff={diff}, criterion=0.5)"
                print(rep+stats, file=f)

        bricks = results['bricks']
        for test in bricks:
            run = bricks[test][0]
            ref = bricks[test][1]
            diff = round((run - ref) / ref, 2)
            if abs(diff) > 0.1:
                rep = f"{test}/{test}.stdout: different 'Total' of bricks "
                stats = f"(ft_run={run}, ft_reference={ref}, rel.diff={diff}, criterion=0.1)"
                print(rep+stats, file=f)
 