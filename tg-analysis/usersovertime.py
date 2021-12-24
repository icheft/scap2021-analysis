#!/usr/bin/env python3
"""
A program to plot the users joining a chat over time. Note that leaving events are not noted.
TODO: support multiple chats.
TODO: support saving to image
"""
import argparse
import os
from json import loads
from datetime import date, timedelta, datetime
from collections import defaultdict
from pprint import pprint

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from mgt2001 import color_palette
import dateutil
plt.style.use('ggplot')


def save_figure(folder, filenames):
    chats_string = '_'.join(filenames)

    if len(chats_string) > 200:
        # file name likely to be so long as to cause issues
        figname = input(
            "This graph is going to have a very long file name. Please enter a custom name(no need to add an extension): ")
    else:
        figname = "User growth overtime in {}".format(chats_string)

    plt.savefig("{}/{}.png".format(folder, figname))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a pie chart showing the most active users in a Telegram chat")
    required = parser.add_argument_group('required arguments')
    required.add_argument(
        '-f', '--files',
        help='paths to the json file(s) (chat logs) to analyse.',
        required=True,
        nargs='+'
    )
    parser.add_argument(
        '-o', '--output-folder',
        help='the folder to save the pie chart image in.'
        'Using this option will make the graph not display on screen.')
    parser.add_argument(
        '-s', '--figure-size',
        help='the size of the figure shown or saved (X and Y size).'
        'Choose an appropriate value for your screen size. Default 12 8.',
        nargs=2, type=int, default=[12, 8]
    )
    parser.add_argument(
        '-m', '--minimum-percentage',
        help='the minimum percentage of activity a person must contribute '
        'to get their own slice of the pie chart. Default 2',
        type=float, default=2
    )
    parser.add_argument(
        '-d', '--date-range',
        help='the range of dates you want to look at data between. '
        'Must be in format YYYY-MM-DD YYYY-MM-DD with the first date '
        'the start of the range, and the second the end. Example: '
        "-d '2017-11-20 2017-05-15'. Make sure you don't put a day "
        'that is too high for the month eg 30th February.',
        default="1000-01-01 4017-01-01"
        # hopefully no chatlogs contain these dates :p
    )

    return parser.parse_args()


def get_dates(arg_dates):
    if " " not in arg_dates:
        print("You must put a space between start and end dates")
        exit()
    daterange = arg_dates.split()
    start_date = datetime.strptime(daterange[0], "%Y-%m-%d").date()
    end_date = datetime.strptime(daterange[1], "%Y-%m-%d").date()
    return (start_date, end_date)


def main():
    """
    main function
    """

    args = parse_args()
    filepaths = args.files
    savefolder = args.output_folder
    figure_size = (args.figure_size[0], args.figure_size[1])
    start_date, end_date = get_dates(args.date_range)
    other_percent = args.minimum_percentage
    filenames = []

    for ind, filepath in enumerate(filepaths):
        with open(filepath, 'r') as f:
            events = (loads(line) for line in f)

            counter = defaultdict(int)
            for event in events:
                if "action" in event and (event["action"] == "invite_members" or event['action'] == "join_group_by_link"):
                    day = dateutil.parser.parse(event['date']).date()
                    counter[day] += 1

        filename = os.path.splitext(os.path.split(filepath)[-1])[0]
        filenames.append(filename)

        # frequencies = {key: l.count(True)/l.count(False) * 100 for key, l in counter.items()}
        users_per_day = sorted(counter.items())

        u_count = 0
        for idx, (day, users) in enumerate(users_per_day):
            u_count += users
            users_per_day[idx] = (day, u_count)

        print(users_per_day)
        if "fug" in filepath:
            plt.plot(*zip(*users_per_day), color="#f4af00")
        elif "shi" in filepath:
            plt.plot(*zip(*users_per_day), color="#D10F24")
    plt.title('member growth in "{}"'.format(filenames))
    plt.legend(filenames, loc='best')

    if savefolder is not None:
        # if there is a given folder to save the figure in, save it there
        save_figure(savefolder, filenames)
    else:
        # if a save folder was not specified, just open a window to display graph
        plt.show()


if __name__ == "__main__":
    main()
