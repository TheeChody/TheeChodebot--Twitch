shit_list = []
with open("coupon_code_raw.txt", "r") as file:
    shit_organized = list(map(str, file.read().splitlines()))

for item in shit_organized:
    if len(item) == 5:
        shit_list.append(item)

with open("coupon_code_sorted.txt", "w") as file:
    file.write(' '.join(shit_list))
