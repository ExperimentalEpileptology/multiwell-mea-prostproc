import argparse
from argparse import ArgumentDefaultsHelpFormatter
import ast
import os

from gooey import Gooey, GooeyParser
import numpy as np
import pandas as pd


@Gooey
def parse_args():
    ############### Make script callable from command line with arguments
    parser = GooeyParser(
            prog="Multiwell MEA Analysis Script",
            description=("This script will further analyze the results output "
                         "by the MCS Multiwell MEA software. Credits to Caro "
                         "and Beytül for the original script."),
            epilog=('example usage:\n\t'
                    'python3 analysis.py /mnt/data/multiwell/csv/ '
                    ' conditions_test.txt 5 spikes_test.csv bursts_test.csv '
                    'net_bursts_test.csv\n\n'
                    'Example contents of a condition file:\n\n'
                    '{\n'
                    '\t\'K2_16\': [\'A1\',\'A2\',\'B1\',\'B2\',\'C1\',\'C2\','
                    '\'D1\',\'D2\'],\n'
                    '\t\'P7_3\': [\'A3\',\'A4\',\'B3\',\'B4\'],\n'
                    '\t\'P7_15\': [\'C3\',\'C4\',\'D3\'],\n'
                    '\t\'P8_10\': [\'A5\',\'A6\',\'B5\',\'B6\'],\n'
                    '\t\'KK2_11\': [\'C5\',\'C6\',\'D5\'],\n'
                    '\t\'empty\': [\'D4\',\'D6\']\n'
                    '}'),
            formatter_class=ArgumentDefaultsHelpFormatter,
            conflict_handler='resolve'
            )

    parser.add_argument("base_dir",
                        type=str,
                        help="base directory (e.g. /mnt/data/multiwell/csv/)",
                        widget="DirChooser")

    parser.add_argument("conditions_file",
                        type=str,
                        help=("name of the file that specifies the"
                        "lines/conditions per well as a python dictionary (e.g."
                        "conditions.txt)"))

    parser.add_argument("mins_recorded",
                        type=int,
                        help="minutes recorded, e.g. 5")

    parser.add_argument("spikes_file",
                        type=str,
                        help="spikes csv file name (e.g. spikes_test.csv)")

    parser.add_argument("bursts_file",
                        type=str,
                        help="bursts csv file name")

    parser.add_argument("net_bursts_file",
                        type=str,
                        help="network bursts csv file name")

    args = parser.parse_args()

    return args

if __name__ == "__main__":
    args = parse_args()
    base = args.base_dir
    conditions_fname = args.conditions_file
    spikes_fname = args.spikes_file
    bursts_fname = args.bursts_file
    net_bursts_fname = args.net_bursts_file
    mins_recorded = args.mins_recorded

    ############### check arguments
    if not os.path.exists(base):
        raise FileNotFoundError(f'{base} does not exist!')

    conditions_file = os.path.join(base, conditions_fname)
    spikes_file = os.path.join(base, spikes_fname)
    bursts_file = os.path.join(base, bursts_fname)
    net_bursts_file = os.path.join(base, net_bursts_fname)

    for fname in [conditions_file, spikes_file, bursts_file, net_bursts_file]:
        if not os.path.isfile(fname):
            raise FileNotFoundError(f"{fname} not found or not a file!")

    ############### Setup output folder
    plate_name = '_'.join(os.path.basename(spikes_file).split('_')[0:-1])
    print(f'Plate name is {plate_name} in {base}')

    # Check if analyzed folder exists, if not create
    out_base = os.path.join(base, plate_name)
    if not os.path.exists(out_base):
        os.makedirs(out_base)
    print(f'Output folder is {out_base}')

    ############### Load data and condition/cell line specs
    with open(conditions_file, 'r') as f:
        conditions = ast.literal_eval(f.read())

    spikes = pd.read_csv(spikes_file)
    bursts = pd.read_csv(bursts_file)
    net_bursts = pd.read_csv(net_bursts_file)
    print('Data loaded')

    condition_labels = []
    for k,v in conditions.items():
        condition_labels += [f'{k}_{sv}' for sv in v]

    ############### Preprocessing
    # Compute End time stamps & inter burst intervals
    for arr in [bursts, net_bursts]:
        arr['End timestamp [µs]'] = (arr['Start timestamp [µs]']
                                      + arr['Duration [µs]'])
    # Compute inter burst intervals for bursts
    for i in range(1, bursts.shape[0]):
        if bursts.loc[i, 'Channel Label'] == bursts.loc[(i-1), 'Channel Label']:
            start_t = bursts.loc[i, "Start timestamp [µs]"]
            end_t = bursts.loc[(i-1), 'End timestamp [µs]']
            bursts.loc[i,"inter burst interval [µs]"] = start_t - end_t

    if bursts.shape[0] < 2:
        bursts["inter burst interval [µs]"] = np.nan

    for i in range(1, net_bursts.shape[0]):
        if net_bursts.loc[i, 'Well Label'] == net_bursts.loc[(i-1), 'Well Label']:
            start_t = net_bursts.loc[i, "Start timestamp [µs]"]
            end_t = net_bursts.loc[(i-1), 'End timestamp [µs]']
            net_bursts.loc[i,"inter burst interval [µs]"] = start_t - end_t

    if net_bursts.shape[0] < 2:
        net_bursts["inter burst interval [µs]"] = np.nan

    print("End timestamps and inter burst intervals computed")

    # Drop unnecessary columns
    unneeded_cols = ['Compound ID', 'Compound Name', 'Experiment',
                     'Dose Label', 'Dose [pM]']
    for arr in [spikes, bursts, net_bursts]:
        arr.drop(unneeded_cols, axis=1, inplace=True)

    # make well label specify the condition/cell line contained in the well
    cond_label = "Cell Line/Condition"
    for line, wells in conditions.items():
        for arr in [spikes, bursts, net_bursts]:
            well_label = arr['Well Label']
            arr.loc[well_label.isin(wells), 'Well Label'] = line + '_' + well_label

    print("Cell lines/conditions assigned to wells")

    ############### Use channel labels as index
    channel_labels = spikes["Channel Label"].unique().tolist()
    ############### Calculate the desired spike counts
    print("Calc spike counts")
    spike_counts = pd.DataFrame(index=channel_labels)
    burst_counts = pd.DataFrame(index=channel_labels)
    spon_spike_counts = pd.DataFrame(index=channel_labels)
    random_spikes_ratio = pd.DataFrame(index=channel_labels)


    # In the following we will use group by statements which essentially
    # perform the the summation of spikes for each group and channels.
    # These however turn the data into the format [Channel ID, Well ID, Value]
    # (i.e. each row contains the desired value (e.g. #spikes) of one channel
    # in one well). However the user wants to have the data in the format
    # [Channel ID, Well 0, Well 1, ..., Well N] (i.e. each row contains the
    # desired value (e.g. #spikes) of one channel in all wells). To achieve
    # this we use the unstack function, which does exactly this and fills empty
    # fields with 0.
    agg_cols = ['Channel Label', 'Well Label']
    spike_counts = (spikes.groupby(['Channel Label', 'Well Label']).size()
        .unstack(fill_value=0).reindex(columns=condition_labels, fill_value=0))
    burst_counts = (bursts.groupby(['Channel Label', 'Well Label']).size()
        .unstack(fill_value=0).reindex(columns=condition_labels, fill_value=0))
    burst_spike_counts = ((bursts.groupby(['Channel Label', 'Well Label'])\
            ['Spike Count'].sum().unstack(fill_value=0)
                           .reindex(columns=condition_labels, fill_value=0)))

    spike_counts_per_min = spike_counts / mins_recorded
    burst_counts_per_min = burst_counts / mins_recorded

    spon_spike_counts = spike_counts - burst_spike_counts
    spon_spike_ratio = (spon_spike_counts / spike_counts * 100).fillna(0)

    spike_counts.index = spike_counts.index.set_names(
        'Spike Count per Well and Channel')
    spike_counts_per_min.index = spike_counts_per_min.index.set_names(
        'Spike Counts per min [1/min] per Well and Channel')
    burst_counts.index = burst_counts.index.set_names(
        'Burst Counts per Well and Channel')
    burst_counts_per_min.index = burst_counts_per_min.index.set_names(
        'Burst Counts per min [1/min] per Well and Channel')
    spon_spike_counts.index = spon_spike_counts.index.set_names(
        "Spontaneous Spike Counts per Well and Channel")
    spon_spike_ratio.index = spon_spike_ratio.index.set_names(
        "Spontaneous Spike Ratio [%] per Well and Channel")

    spike_counts.to_excel(os.path.join(out_base, 'spike_counts.xlsx'))
    spike_counts_per_min.to_excel(
            os.path.join(out_base, 'spike_counts_per_min.xlsx'))
    burst_counts.to_excel(os.path.join(out_base, "burst_counts.xlsx"))
    burst_counts_per_min.to_excel(
            os.path.join(out_base, "burst_counts_per_min.xlsx"))
    spon_spike_counts.to_excel(
            os.path.join(out_base, f'spont_spike_counts.xlsx'))
    spon_spike_ratio.to_excel(
            os.path.join(out_base, f'spont_spike_ratio.xlsx'))

    ############### Bursts
    print("Calculate burst quantities")
    avg_burst_duration = pd.DataFrame(index=channel_labels)
    avg_spike_count = pd.DataFrame(index=channel_labels)
    avg_spike_freq = pd.DataFrame(index=channel_labels)
    avg_inter_burst_interval = pd.DataFrame(index=channel_labels)

    avg_burst_duration = (bursts.groupby(agg_cols)['Duration [µs]'].mean()
        .unstack()).reindex(columns=condition_labels)
    avg_spike_freq = (bursts.groupby(agg_cols)['Spike Frequency [Hz]'].mean()
        .unstack()).reindex(columns=condition_labels)
    avg_spike_count = bursts.groupby(agg_cols)['Spike Count'].mean().unstack().reindex(columns=condition_labels)
    avg_inter_burst_interval = (bursts.groupby(agg_cols)['inter burst interval [µs]']
        .mean().unstack()).reindex(columns=condition_labels)

    avg_burst_duration.index = avg_burst_duration.index.set_names(
        "Burst Average Duration [µs] per Well and Channel")
    avg_spike_freq.index = avg_spike_freq.index.set_names(
        "Burst Average Spike Frequency [Hz] per Well and Channel")
    avg_spike_count.index = avg_spike_count.index.set_names(
        "Burst Average Spike Count per Well and Channel")
    avg_inter_burst_interval.index = avg_inter_burst_interval.index.set_names(
        "Average Inter-Burst Interval [µs] per Well and Channel")

    avg_burst_duration.to_excel(os.path.join(out_base,
                                             "avg_burst_duration.xlsx"))
    avg_spike_freq.to_excel(os.path.join(out_base,
                                         "avg_spike_freq_per_burst.xlsx"))
    avg_spike_count.to_excel(os.path.join(out_base,
                                          "avg_spike_count_per_burst.xlsx"))
    avg_inter_burst_interval.to_excel(os.path.join(out_base,
                                          "avg_inter_burst_interval.xlsx"))


    ############### Net Bursts
    # inter burst interval und var of coef
    nb_numbers = pd.DataFrame(columns=condition_labels)
    nb_duration = pd.DataFrame(columns=condition_labels)
    nb_sike_count = pd.DataFrame(columns=condition_labels)
    nb_spike_freq = pd.DataFrame(columns=condition_labels)
    nb_avg_inter_burst_interval = pd.DataFrame(columns=condition_labels)
    nb_ibi_coef_of_var = pd.DataFrame(columns=condition_labels)

    nb_numbers = (net_bursts.groupby(['Well Label']).size()
        .reindex(index=condition_labels, fill_value=0) / mins_recorded)
    nb_duration = net_bursts.groupby(['Well Label'])['Duration [µs]'].mean().reindex(index=condition_labels)
    nb_spike_count = net_bursts.groupby(['Well Label'])['Spike Count'].mean().reindex(index=condition_labels)
    nb_spike_freq = (net_bursts.groupby(['Well Label'])['Spike Frequency [Hz]']
        .mean()).reindex(index=condition_labels)
    nb_avg_inter_burst_interval = (net_bursts.groupby(['Well Label'])\
            ['inter burst interval [µs]'].mean()).reindex(index=condition_labels)
    nb_ibi_coef_of_var = (net_bursts.groupby(['Well Label'])\
            ['inter burst interval [µs]'].std() / nb_avg_inter_burst_interval ).reindex(index=condition_labels)

    nb_numbers.rename("Network Burst Count per Well", inplace=True)
    nb_duration.rename("Network Burst Average Duration [µs] per Well",
                       inplace=True)
    nb_spike_count.rename("Network Burst Average Spike Count per Well",
                          inplace=True)
    nb_spike_freq.rename("Network Burst Average Spike Frequency [Hz] per Well",
                         inplace=True)
    nb_avg_inter_burst_interval.rename("Network Average Inter-Burst Interval"
                                       "[µs] per Well", inplace=True)
    nb_ibi_coef_of_var.rename("Network Inter-Burst Interval Coefficient of"
                              " Variation per Well", inplace=True)

    nb_numbers.to_excel(os.path.join(out_base, "net_bursts_count_per_min.xlsx"))
    nb_duration.to_excel(os.path.join(out_base, "net_bursts_avg_duration.xlsx"))
    nb_spike_count.to_excel(os.path.join(out_base,
                                         "net_bursts_spike_count_per_min.xlsx"))
    nb_spike_freq.to_excel(os.path.join(out_base, "net_bursts_spike_freq.xlsx"))
    nb_avg_inter_burst_interval.to_excel(os.path.join(out_base,
                                                      "net_bursts_avg_ibi.xlsx"))
    nb_ibi_coef_of_var.to_excel(os.path.join(out_base,
                                                      "net_bursts_ibi_coef_of_var.xlsx"))
