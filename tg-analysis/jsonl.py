import json


file_name = input()

with open(f'../data/{file_name}.json', 'r') as jsonfile:
    # if args.date_range is not None:
    #    chat_counter = make_ddict_in_date_range(
    #            jsonfile,binsize,start_date,end_date)
    # else:
    #    chat_counter = make_ddict(jsonfile,binsize)
    entries = json.load(jsonfile)

    with open(f'../data/{file_name}.jsonl', 'w') as outfile:
        for entry in entries:
            json.dump(entry, outfile)
            outfile.write('\n')
