from config import LOGS_PATH, T_REF, T_RUN
import func
import os

folders = func.go_to_directory(LOGS_PATH)
reps = []

for group in folders: #Groups = 13-ROTATED_FLOWS  14-HEAT_TRANSFER_IN_SOLID  15-JOULE_HEATING_IN_SOLID
    os.chdir(group)
    tests = list(map(os.path.abspath, os.listdir())) #list of testcases
    tests = list(map(lambda x: str(x), tests))
    for test in sorted(tests):
        os.chdir(test) #inside test cases ()

        report = func.check_test_exists()
        if report[T_REF] == 0 or report[T_RUN] == 0:
            reps.append(report)
            func.make_report(report)
            continue
        
        report['missing_files'], report['extra_files'] = func.check_test_missing()
        if report['missing_files'] != [] or report['extra_files'] != []:
            reps.append(report)
            func.make_report(report)
            continue

        report['cases_errors'] = func.check_test_errors()
        report['solver'] = func.check_test_solver()
        report['memory_test'] = func.check_test_memory()
        report['bricks'] = func.check_test_bricks()
        func.make_report(report)
        if func.file_is_empty('report.txt'):
            std_info = 'OK: '
            std_info += os.path.join(report['group'], report['case'])
            std_info += '/'
            print(std_info)
        else:
            std_info = 'FAIL: '
            std_info += os.path.join(report['group'], report['case'])
            std_info += '/'
            print(std_info)
            with open('report.txt', 'r') as f:
                print(f.read().strip('\n'))
        reps.append(report)




# for rep in reps:
#     print(rep)