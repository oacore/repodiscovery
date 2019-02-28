# repodiscovery

Discover the repository software by crawling the repository homepage.

## Use instructions

The code in the repository uses Python 3+.

Create a CSV containing a list of repositories to be checked. It should look
like this (without the header):

| Homepage URL                    | Country code | CORE ID | OPEN DOAR ID | ROAR ID |
|---------------------------------|--------------|---------|--------------|---------|
| http://aura.abdn.ac.uk          | GB           | 1       | 1767         |         |
| http://repository.abertay.ac.uk | GB           | 2       | 1589         |         |
| http://gtcni.openrepository.com | GB           | 3       | 549          |         |
| http://eprints.aktors.org       | GB           | 4       | 1            | 31      |
| http://repository.alt.ac.uk     | GB           | 5       |              | 961     |

There's an [example input file](example_input.csv) you can use to test the app.

Afterwards, run:

1. ``pip install --upgrade pip && pip install -r requirements.txt``
2. ``mkdir results && mkdir repo_pages``
3. ``python reposwdiscovery.py /path/to/your/input_file.csv 0``
   * Using the example input provided in this repository: ``python reposwdiscovery.py example_input.csv 0``
4. ``cat results/results-Thread-* >> results-$(date +"%d%m%y").csv``
5. ``cat results/errors-Thread-* >> errors-$(date +"%d%m%y").csv``

This will produce two CSV files with results, one containing successfully checked repositories and the other containing unsuccessfully processed repositories.