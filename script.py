import os
import re
# import time
# start  = time.time()
LOGS_PATH = os.path.join(os.getcwd(), '/home/alexey/Documents/Work/TestTask/task1/logs')

def parse_bricks(s):
    return int(re.search(r'Total=\d+', s).group().split('=')[-1])

def parse_memory(s):
    return float(s.split()[-2])

def make_report(results, path):
    with open(os.path.join(path, 'report.txt'), 'w') as f:

        if not results['ft_run'] or  not results['ft_reference']:
            if not results['ft_run']:
                print("directory missing: ft_run", file=f)
            if not results['ft_reference']:
                print("directory missing: ft_reference", file=f)
            f.close()
            return

        if results['missing_files'] != [] or results['extra_files'] != []:
            if results['missing_files'] != []:
                missing = ', '.join(results['missing_files'])
                print(f"In ft_run there are missing files present in ft_reference: {missing}", file=f)
            if results['extra_files'] != []:
                extra = ', '.join(results['extra_files'])
                print(f"In ft_run there are extra files not present in ft_reference: {extra}", file=f)
            f.close()
            return

        reps = []

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

        reps.sort()
        for report in reps:
            print(report, file=f)

def read_report(report, path):
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

folders = list(map(lambda x: os.path.join(LOGS_PATH, x), sorted(os.listdir(LOGS_PATH))))

for group in folders: #Groups = 13-ROTATED_FLOWS  14-HEAT_TRANSFER_IN_SOLID  15-JOULE_HEATING_IN_SOLID
    tests = list(map(lambda x: os.path.join(LOGS_PATH, group, x), sorted(os.listdir(group)))) # List of testcases
    for test in tests:
        report = {
            'group': os.path.split(os.path.split(test)[0])[-1],
            'case': os.path.split(test)[-1],
            'ft_run': 1 if os.path.exists(os.path.join(test, 'ft_run')) else 0,
            'ft_reference': 1 if os.path.exists(os.path.join(test, 'ft_reference')) else 0
        }

        if not report['ft_reference'] or not report['ft_run']:
            make_report(report, test)
            read_report(report, test)
            continue

        ft_run = os.listdir(os.path.join(test, 'ft_run'))
        ft_ref = os.listdir(os.path.join(test, 'ft_reference'))
        ft_run = set(map(int, ft_run))
        ft_ref = set(map(int, ft_ref))
        report['missing_files'] = list(map(lambda x: f"'{str(x)}/{str(x)}.stdout'", ft_ref - ft_run))
        report['extra_files'] = list(map(lambda x: f"'{str(x)}/{str(x)}.stdout'", ft_run - ft_ref))

        if report['missing_files'] != [] or report['extra_files'] != []:
            make_report(report, test)
            read_report(report, test)
            continue

        errors = {}
        solver_exist = {}
        memory_peak = {}
        bricks = {}
        for case in ft_run:
            with open(os.path.join(test,'ft_run', f'{str(case)}/{str(case)}.stdout'), 'r') as f:
                run_text = f.readlines()
            with open(os.path.join(test, 'ft_reference', f'{str(case)}/{str(case)}.stdout'), 'r') as f:
                ref_text = f.readlines()
            errors[case] = []
            solver_exist[case] = True
            run_peaks = []
            ref_peaks = []
            for num, line in enumerate(run_text, start=1):
                if ' error' in line.lower() or '\terror' in line.lower():
                    errors[case].append((num, run_text[num - 1].strip('\n')))
                if line.startswith('Solver finished at'):
                    solver_exist[case] = False
                if line.startswith('Memory Working Set Current'):
                    run_peaks.append(parse_memory(line))
                if line.startswith('MESH::Bricks: Total='):
                    run_bricks = parse_bricks(line)
            
            for line in ref_text:
                if line.startswith('Memory Working Set Current'):
                    ref_peaks.append(parse_memory(line))
                if line.startswith('MESH::Bricks: Total='):
                    ref_bricks = parse_bricks(line)

            memory_peak[case] = (run_peaks[-1], ref_peaks[-1])
            bricks[case] = (run_bricks, ref_bricks)

        report['solver'] = solver_exist
        report['cases_errors'] = errors
        report['memory_test'] = memory_peak
        report['bricks'] = bricks
        make_report(report, test)
        read_report(report, test)
# end = time.time() - start
# print(f'It took {end} time')