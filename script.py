from config import LOGS_PATH, T_REF, T_RUN
import func
import os

folders = func.go_to_directory(LOGS_PATH)
data = []

for group in folders: #Groups = 13-ROTATED_FLOWS  14-HEAT_TRANSFER_IN_SOLID  15-JOULE_HEATING_IN_SOLID
    os.chdir(group)
    tests = list(map(os.path.abspath, sorted(os.listdir()))) # List of testcases
    for test in tests:
        os.chdir(test) # Inside test cases 1, 2 etc

        report = func.check_test_exists()
        if report[T_REF] == 0 or report[T_RUN] == 0:
            func.make_report(report)
            func.read_report(report)
            continue
        
        report['missing_files'], report['extra_files'] = func.check_test_missing()
        if report['missing_files'] != [] or report['extra_files'] != []:
            func.make_report(report)
            func.read_report(report)
            continue

        report['cases_errors'] = func.check_test_errors()
        report['solver'] = func.check_test_solver()
        report['memory_test'] = func.check_test_memory()
        report['bricks'] = func.check_test_bricks()
        func.make_report(report)
        func.read_report(report)
