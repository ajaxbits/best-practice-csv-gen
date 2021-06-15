import json
import os
import sys
from typing import List

import pandas as pd
from pandas.core import base
import requests

cert = False


def sanitize_sort_policy(json: dict) -> dict:
    # no_fly_keys = ["name", "ID", "parentID", "activityMonitoring"]
    # clean_json = {}
    # for key in no_fly_keys:
    #     if json.get(key) is not None:
    #         del json[key]
    clean_json = json
    sorted_keys = sorted(json.keys())
    for key in sorted_keys:
        clean_json[key] = json[key]
    return clean_json


def load_best_practices(file_path: str):
    with open(file_path, "r") as best_practices_file:
        best_practices = best_practices_file.read()
        best_practices_json = json.loads(best_practices)
        return sanitize_sort_policy(best_practices_json)


def gather_all_policy_json(url_link_final: str, tenant1key: str) -> List[dict]:
    """
    takes in DSM url and API key, transforms into a list of json policies

    Args:
        url_link_final (str): full access DS api key
        tenant1key (str): full access DS api key

    Returns:
        List[dict]: a list of policy json objects
    """
    allofpolicy = []
    url = url_link_final + "api/policies"
    headers = {
        "api-secret-key": tenant1key,
        "api-version": "v1",
        "Content-Type": "application/json",
    }
    try:
        response = requests.request(
            "GET",
            url,
            headers=headers,
            data={},
            verify=cert,
        )
    except Exception as e:
        print(e)
        print(
            "Having trouble connecting to the old DSM. Please ensure the url and routes are correct."
        )
        print("Aborting...")
        sys.exit(0)
    response_str = str(response.text)
    all_policies_json = json.loads(response_str)
    for policy in all_policies_json["policies"]:
        policy = sanitize_sort_policy(policy)
        allofpolicy.append(policy)
    return allofpolicy


def substring_row_eliminator(
    column, no_fly_list: list, data_frame: pd.DataFrame
) -> pd.DataFrame:
    for string in no_fly_list:
        data_frame = data_frame[~data_frame[column].str.contains(string)]
    return data_frame


def extrapolate_column(data_frame: pd.DataFrame, column: str):
    return data_frame[column].str[12:24]


def accounts_extrapolated(data_frame):
    mask = data_frame["Computer Group"].str.len() > 30
    data_frame.loc[mask, "Cloud Account Extrapolated"] = extrapolate_column(
        data_frame, "Computer Group"
    )
    return data_frame


def accounts_extrapolated_use_this_one(data_frame):
    data_frame["Cloud Account Extrapolated (Use This Column)"] = data_frame[
        "Cloud Account Extrapolated"
    ].fillna(method="ffill")
    return data_frame


def order_data_frame(data_frame):
    cols = [
        "Id",
        "Hostname",
        "Display Name",
        "Computer Group",
        "Instance Type",
        "Start Date",
        "Start Time",
        "Stop Date",
        "Stop Time",
        "Duration (Seconds)",
        "Cloud Account Extrapolated (Use This Column)",
        "Cloud Account Extrapolated",
        "Cloud Account",
        "AM",
        "WRS",
        "AC",
        "IM",
        "LI",
        "FW",
        "DPI",
    ]
    return data_frame[cols]


# INFILE = sys.argv[1]
# OUTFILE = sys.argv[2]

# df = pd.read_csv(INFILE)

# no_fly_list = [
#     "Computers > Linux \(group 2\) > DPC",
#     "Computers > Windows \(group 1\) > DPC",
#     "Computers > Windows \(group 1\) > CC",
#     "Computers > Linux \(group 2\) > CC",
# ]

# print("deleting CC and DPC rows...")
# df = substring_row_eliminator("Computer Group", no_fly_list, df)

# print("Extrapolating Cloud accounts...")
# df = accounts_extrapolated(df)

# print("Further Extrapolation and copying...")
# df = accounts_extrapolated_use_this_one(df)

# print("Sorting rows and columns...")
# df = order_data_frame(df)
# df = df.sort_values(["Computer Group", "Id"])

# print("Creating CSV...")
# df.to_csv(OUTFILE, index=False)
def exclude_keys(set: list):
    no_fly_keys = ["name", "ID", "parentID", "activityMonitoring", "rule_IDs"]
    for item in set:
        if item in no_fly_keys:
            set.remove(item)
    return set


def recursive_compare(json_a, json_b, policy_id, policy_name, df_dict, level="root"):
    if isinstance(json_a, dict) and isinstance(json_b, dict):
        if json_a.keys() != json_b.keys():
            s1 = set(json_a.keys())
            s2 = set(json_b.keys())
            common_keys = s1 & s2
        else:
            common_keys = exclude_keys(set(json_a.keys()))

        for common_key in common_keys:
            recursive_compare(
                json_a[common_key],
                json_b[common_key],
                policy_id,
                policy_name,
                df_dict,
                level=f"{level} > {common_key}",
            )
    else:
        if json_a != json_b:
            df_dict["policyName"].append(policy_name)
            df_dict["policyID"].append(policy_id)
            df_dict["policySetting"].append(level)
            df_dict["currentConfiguration"].append(json_a)
            df_dict["trendRecommendedConfiguration"].append(json_b)
    return df_dict


if __name__ == "__main__":
    best_practices = load_best_practices("best-practice-policy.json")
    allofpolicy = gather_all_policy_json(
        "https://cloudone.trendmicro.com/", os.environ.get("DS_API_KEY")
    )

    df_dict = {
        "policyID": [],
        "policyName": [],
        "policySetting": [],
        "trendRecommendedConfiguration": [],
        "currentConfiguration": [],
    }

    for policy in allofpolicy:
        policy_id = policy.get("ID")
        policy_name = policy.get("Name")
        df_dict = recursive_compare(
            policy, best_practices, policy_id, policy_name, df_dict
        )

    print("hello")
