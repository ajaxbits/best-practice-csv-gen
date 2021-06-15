import pandas as pd
import sys

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


INFILE = sys.argv[1]
OUTFILE = sys.argv[2]

df = pd.read_csv(INFILE)

no_fly_list = [
    "Computers > Linux \(group 2\) > DPC",
    "Computers > Windows \(group 1\) > DPC",
    "Computers > Windows \(group 1\) > CC",
    "Computers > Linux \(group 2\) > CC",
]

print("deleting CC and DPC rows...")
df = substring_row_eliminator("Computer Group", no_fly_list, df)

print("Extrapolating Cloud accounts...")
df = accounts_extrapolated(df)

print("Further Extrapolation and copying...")
df = accounts_extrapolated_use_this_one(df)

print("Sorting rows and columns...")
df = order_data_frame(df)
df = df.sort_values(["Computer Group", "Id"])

print("Creating CSV...")
df.to_csv(OUTFILE, index=False)
