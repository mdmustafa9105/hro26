import os

targets = ["account_5684", "account_3136", "account_5482", "account_7012", "account_410", "account_5037", "account_5521", "account_3610"]

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    for line in f:
        for t in targets:
            if t in line:
                print(line.strip())
