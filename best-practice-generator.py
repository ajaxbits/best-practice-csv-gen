#!/usr/bin/env python3

import json
import sys
from typing import List

import pandas as pd
import requests

cert = False


def sanitize_sort_policy(json: dict) -> dict:
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


def recursive_df_dict_generate(
    json_a, json_b, policy_id, policy_name, df_dict, level="root"
):
    if isinstance(json_a, dict) and isinstance(json_b, dict):
        if json_a.keys() != json_b.keys():
            s1 = set(json_a.keys())
            s2 = set(json_b.keys())
            common_keys = s1 & s2
        else:
            common_keys = set(json_a.keys())

        for common_key in common_keys:
            recursive_df_dict_generate(
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


def sanitize_dataframe(dataframe, column):
    no_fly_keys = [
        "ruleID",
        "root > name",
        "root > ID",
        "root > parentID",
        "statusMessage",
        "root > description",
    ]
    for key in no_fly_keys:
        dataframe = dataframe[~dataframe[column].str.contains(key)]
    return dataframe


if __name__ == "__main__":
    REPORT_NAME = sys.argv[1]
    BEST_PRACTICES = sys.argv[2]
    URL = sys.argv[3]
    API_KEY = sys.argv[4]

    best_practices = load_best_practices(BEST_PRACTICES)
    allofpolicy = gather_all_policy_json(URL, API_KEY)

    df_dict = {
        "policyID": [],
        "policyName": [],
        "policySetting": [],
        "trendRecommendedConfiguration": [],
        "currentConfiguration": [],
    }

    for policy in allofpolicy:
        policy_id = policy.get("ID")
        policy_name = policy.get("name")
        df_dict = recursive_df_dict_generate(
            policy, best_practices, policy_id, policy_name, df_dict
        )

    df = pd.DataFrame.from_dict(df_dict)
    df = sanitize_dataframe(df, "policySetting")
    df = df.sort_values(by=["policyID", "policySetting"])
    df.to_csv(REPORT_NAME, index=False)
