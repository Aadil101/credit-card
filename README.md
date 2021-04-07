# DCU
This is a program that pays a Digital Federal Credit Union (DCU) credit card balance for the current month. It does so by parsing the current month's credit card statement, and transferring the necessary amount in dollars from the user's checking account (ie. one with sufficient funding) to the user's credit card. The checking account is also replenished using the user's savings account.

## Installation

Use the package manager `pip` to install DCU:

`pip install -r requirements.txt`

## Usage

This program makes a few assumptions:
- You have Google Chrome installed.
- You have a working DCU Free Checking/Savings/Credit Card.
- You have a Gmail account.

Please fill in `config.yml` accordingly:
- `user-data-dir`: Path to Google Chrome profile on your machine.
- `dcu`
  - `member-number`: Your seven DCU member number.
  - `password`: Your DCU password.
- `email`
  - `address`: Your Gmail address.
  - `password`: Your Gmail password.
- `from-account`: Account name (eg. checking account) from which you'd like to pay credit card statement with.
- `pool-account`: Account name (eg. savings account) from which money may be transferred to `from-account` if necessary.
- `to-account`: Account name (eg. credit card) which you'd like to pay off monthly.
- `from-account-keep`: Amount you'd like to keep in `from-account` at all times.

You may want to run this program monthly on your machine. If you're running MacOS or Linux, this can be done by running a `cron` job. Cron jobs are nice in that you can use them to schedule running a program every however many seconds/minutes/days/months etc. Make sure your machine is ready to run cron jobs by following the helpful instructions given [here](https://blog.bejarano.io/fixing-cron-jobs-in-mojave/).

You can create a cron job by typing `crontab -e` in your terminal, which should open for you an editor. In this editor, you want to accomplish something like this: every first day of each month (which we indicate using the cron command `0 0 1 * *`) go to this repo on our machine (for me, it is located at `/Users/pickle/Documents/code_is_life/dcu/`) and run the python script `dcu.py` (turns out my Python 3.x path is `/usr/bin/python`). Putting it all together, here's what I have in my editor:

`0 0 1 * * cd /Users/pickle/Documents/code_is_life/dcu/ && /usr/bin/python dcu.py`

Hit save, exit the editor, and voila :)

## Contributing 

Pull requests are always welcome.

## License

Distributed under the MIT License. See LICENSE for more information.