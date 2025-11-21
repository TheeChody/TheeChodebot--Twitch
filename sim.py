import os
import sys
import random
import logging
import datetime
from threading import Thread
from timeit import default_timer as timer

if getattr(sys, 'frozen', False):
    application_path = f"{os.path.dirname(sys.executable)}\\_internal"
else:
    application_path = os.path.dirname(__file__)

logs_dir = f"{application_path}\\logs\\"
arch_logs_dir = f"{application_path}\\logs\\archive_log\\"

lines = {
    0: {
        "cost": 0,
        "effect": 0,
        "level": 0,
        "name": "Standard"
    },
    1: {
        "cost": 5000,
        "effect": 5,
        "level": 1,
        "name": "Common"
    },
    2: {
        "cost": 25000,
        "effect": 10,
        "level": 2,
        "name": "UnCommon"
    },
    3: {
        "cost": 500000,
        "effect": 20,
        "level": 3,
        "name": "Rare"
    },
    4: {
        "cost": 5000000,
        "effect": 30,
        "level": 4,
        "name": "Epic"
    },
    5: {
        "cost": 25000000,
        "effect": 45,
        "level": 5,
        "name": "Legendary"
    },
    6: {
        "cost": 500000000,
        "effect": 60,
        "level": 6,
        "name": "TheeLine"
    }
}
lures = {
    0: {
        "cost": 0,
        "effect": 0,
        "level": 0,
        "name": "Standard",
        "pLow": 0.0,
        "pHigh": 100.0
    },
    1: {
        "cost": 5000,
        "effect": 2.5,
        "level": 1,
        "name": "Common",
        "pLow": 85.0,
        "pHigh": 98.0
    },
    2: {
        "cost": 25000,
        "effect": 5,
        "level": 2,
        "name": "UnCommon",
        "pLow": 72.5,
        "pHigh": 94.0
    },
    3: {
        "cost": 500000,
        "effect": 10,
        "level": 3,
        "name": "Rare",
        "pLow": 50.0,
        "pHigh": 88.0
    },
    4: {
        "cost": 5000000,
        "effect": 15,
        "level": 4,
        "name": "Epic",
        "pLow": 34.0,
        "pHigh": 80.0
    },
    5: {
        "cost": 25000000,
        "effect": 20,
        "level": 5,
        "name": "Legendary",
        "pLow": 16.9,
        "pHigh": 69.0
    },
    6: {
        "cost": 500000000,
        "effect": 30,
        "level": 6,
        "name": "TheeLure",
        "pLow": 16.9,
        "pHigh": 50.0
    }
}
reels = {
    0: {
        "cost": 0,
        "effect": 0,
        "level": 0,
        "name": "Standard",
        "pLow": 0,
        "pHigh": 100
    },
    1: {
        "cost": 5000,
        "effect": 5,
        "level": 1,
        "name": "Common",
        "pLow": 0,
        "pHigh": 100
    },
    2: {
        "cost": 25000,
        "effect": 10,
        "level": 2,
        "name": "UnCommon",
        "pLow": 0,
        "pHigh": 100
    },
    3: {
        "cost": 500000,
        "effect": 15,
        "level": 3,
        "name": "Rare",
        "pLow": 0,
        "pHigh": 100
    },
    4: {
        "cost": 5000000,
        "effect": 30,
        "level": 4,
        "name": "Epic",
        "pLow": 0,
        "pHigh": 100
    },
    5: {
        "cost": 25000000,
        "effect": 45,
        "level": 5,
        "name": "Legendary",
        "pLow": 0,
        "pHigh": 100
    },
    6: {
        "cost": 500000000,
        "effect": 60,
        "level": 6,
        "name": "TheeLure",
        "pLow": 0,
        "pHigh": 100
    },
}
rods = {
    0: {
        "cost": 0,
        "effect": 0,
        "level": 0,
        "name": "Standard",
        "pLow": 0,
        "pHigh": 100
    },
    1: {
        "cost": 5000,
        "effect": 2.5,
        "level": 1,
        "name": "Common",
        "pLow": 0,
        "pHigh": 100
    },
    2: {
        "cost": 25000,
        "effect": 5,
        "level": 2,
        "name": "UnCommon",
        "pLow": 0,
        "pHigh": 100
    },
    3: {
        "cost": 500000,
        "effect": 10,
        "level": 3,
        "name": "Rare",
        "pLow": 0,
        "pHigh": 100
    },
    4: {
        "cost": 5000000,
        "effect": 15,
        "level": 4,
        "name": "Epic",
        "pLow": 0,
        "pHigh": 100
    },
    5: {
        "cost": 25000000,
        "effect": 20,
        "level": 5,
        "name": "Legendary",
        "pLow": 0,
        "pHigh": 100
    },
    6: {
        "cost": 500000000,
        "effect": 30,
        "level": 6,
        "name": "TheeLure",
        "pLow": 0,
        "pHigh": 100
    },
}


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def run_sim():
    start = timer()

    item_list = [[], []]
    item_list_changed = []
    # prob_list = []
    choices_dict = {}
    prob_cap = [lures[lure_level]['pLow'], lures[lure_level]['pHigh']]

    # with open("data/bot/fish_rewards - Copy", "r") as file:
    with open("data/bot/fish_rewards", "r") as file:
        items_raw = file.read().splitlines()
    total_items = len(items_raw)

    for item in items_raw:
        prob = 100.00
        item_name, item_value = item.split(", ", maxsplit=2)

        # prob -= (abs(float(item_value)) / len(str(abs(float(item_value))))) / 50
        prob -= (abs(float(f'{float(item_value):.2f}')) / len(str(abs(float(f'{float(item_value):.2f}'))))) / 50

        if lure_level > 0 and prob_cap[0] <= prob < prob_cap[1]:
            old_prob = prob
            prob += lures[lure_level]['effect']
            item_list_changed.append([item_name, item_value, prob, old_prob])
        elif lure_level > 0 and prob > prob_cap[1]:
            old_prob = prob
            prob -= lures[lure_level]['effect'] / 2
            item_list_changed.append([item_name, item_value, prob, old_prob])
        if prob < 0:
            while len(f'{int(abs(prob))}') > 1:
                print("len of prob > 1")
                prob /= 10
                print(f"new prob {prob} -- {abs(prob)} -- {int(prob)}")
            prob = abs(prob)

        item_list[0].append([item_name, item_value, prob])
        item_list[1].append(prob)

    if len(item_list_changed) > 0:
        item_list_changed_sorted = sorted(item_list_changed, key=lambda x: x[2], reverse=True)
        for item in item_list_changed_sorted:
            logger.info(f"{float(item[2]):.7f}::{float(item[3]):.7f}/{item[1]}/{item[0]}")
        logger.info(f"{len(item_list_changed)} items changed due to LURE RARITY")
    else:
        item_list_sorted = sorted(item_list[0], key=lambda x: x[2], reverse=True)
        for item in item_list_sorted:
            logger.info(f"{float(item[2]):.7f}/{item[1]}/{item[0]}")
        logger.info("NO CHANGE IN PROBS FROM LURES")

    for x in range(iterations):
        choice = random.choices(item_list[0], item_list[1])[0]
        if choice[0] not in choices_dict:
            choices_dict[choice[0]] = [float(choice[1]), 1, choice[2]]
        else:
            choices_dict[choice[0]][1] += 1

    list_to_sort = []
    for key, value in choices_dict.items():
        list_to_sort.append([key, value[0], value[1], value[2]])

    list_to_sort_sorted = sorted(list_to_sort, key=lambda x: x[3], reverse=True)
    for item in list_to_sort_sorted:
        logger.info(f"{item[3]:.7f}: {item[2]}: {item[1]}: {item[0]}")

    logger.info(f"\nFinished -- Total casts; {iterations:,}\nLureLvL(Plow/Phigh;Peffect); {lure_level}({prob_cap[0]}/{prob_cap[1]};{lures[lure_level]['effect']})\nTotal Unique Items Animals/Total Available; {len(list_to_sort_sorted)}/{total_items}\nTime Taken; {timer() - start}")
    input("\nHit Enter To Proceed To Next Sim\n")


if __name__ == "__main__":
    def shutdown():
        try:
            logging.shutdown()
            os.rename(f"{logs_dir}{logger_filename}", f"{arch_logs_dir}{logger_filename}")
        except Exception as f:
            print(f"Error in shutdown -- {f}")
            quit()
    try:
        logger_filename = f"{str(datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S')).replace(' ', '--').replace(':', '-')}_sim_log.log"
        logger = logging.getLogger("logger")
        handler = logging.FileHandler(f"{logs_dir}{logger_filename}", mode="w", encoding="utf-8")
        console_handler = logging.StreamHandler()
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        while True:
            while True:
                lure_level = input(f"Enter Lure Level {min(lures.keys())}-{max(lures.keys())}\n")
                if lure_level.isdigit():
                    lure_level = int(lure_level)
                    if lure_level > max(lures.keys()):
                        print(f"Number must be lower than {max(lures.keys())}")
                    else:
                        break
                else:
                    print("Just Enter A Number!!")
            while True:
                iterations = input(f"Enter how many Casts To Simulate (Just A Whole Number)\n")
                if iterations.isdigit():
                    iterations = int(iterations)
                    break
                else:
                    print("Just Enter A Number!!")
            cls()
            Thread(target=run_sim).run()
    except KeyboardInterrupt:
        print("Exiting")
        shutdown()
        quit()
    except Exception as e:
        print(f"Error Occurred -- {e}")
        shutdown()
        quit()
