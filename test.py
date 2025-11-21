# import random
#
# hk_already_watched = [7, 15]
#
# while True:
#     choice = random.randint(1, 22)
#     if choice not in hk_already_watched:
#         print(f"Season {choice}!")
#         break

# import datetime
# from functions import read_file, clock, clock_lube, clock_cuss, clock_data, clock_total, clock_sofar, clock_max, \
#     clock_phase, clock_time_phase_accel, clock_time_mode, clock_pause, clock_mode, clock_time_started, \
#     clock_time_phase_slow, clock_phase_slow_rate, clock_cuss_state, clock_lube_state, \
#     clock_mode_old, clock_pause_old, clock_phase_old, save_json
#
# try:
#     clock_dict = {
#         "time_added": read_file(clock_total, float),
#         "time_cuss": read_file(clock_cuss, float),
#         "time_direction_up": read_file(clock_time_mode, float),
#         "time_left": read_file(clock, float),
#         "time_lube": read_file(clock_lube, float),
#         "time_max": read_file(clock_max, float),
#         "time_pause": read_file(clock_pause, float),
#         "time_phase_accel": read_file(clock_time_phase_accel, float),
#         "time_phase_slow": read_file(clock_time_phase_slow, float),
#         "time_phase_slow_rate": read_file(clock_phase_slow_rate, int),
#         "time_so_far": read_file(clock_sofar, float),
#         "time_started": read_file(clock_time_started, datetime),
#         "state_cuss": read_file(clock_cuss_state, bool),
#         "state_direction": read_file(clock_mode, str),
#         "state_direction_old": read_file(clock_mode_old, str),
#         "state_lube": read_file(clock_lube_state, bool),
#         "state_pause": read_file(clock_pause_old, bool),
#         "state_phase": read_file(clock_phase, str),
#         "state_phase_old": read_file(clock_phase_old, str),
#     }
#
#     save_json(clock_dict, clock_data)
# except Exception as _error:
#     print(_error)
