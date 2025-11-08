# Hate the Game

<img src="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.pinimg.com%2F736x%2F35%2Fc9%2F33%2F35c93381f2a65582e6dfc5d077e71cbd.jpg&f=1&nofb=1&ipt=905c02b0639659df279ef6e1b9288303d74e8817315646f4bad5815999c2dc49" align="right"
alt="Sweaty" width="260" height="178">

When you wake up at 5:30am to book a desk and they're all gone 😐. If you can't beat them... join them.

## How It Works

Firstly, this took way longer than it should have. The CondecoBooker just mimics the same http requests made by the browser. It is not fully fleshed yet (and I probs won't be bothered to add more functionality).

_TODO: Verify booking was successful as a 200 status code unfortunately is not enough_

## Usage

### Specify the Environment

The project expects a .env file in the project root. e.g.

```sh
# .env file
CONDECO_HOST="exampledomain.com"
CONDECO_USER_EMAIL="exampleemail@blah.com"
CONDECO_USER_PWD="plaintextpassword"
```

### Poetry :)

Install poetry if you haven't already. https://python-poetry.org/

<details><summary><b>Show instructions</b></summary>

1. Install the dependencies:

   ```sh
   poetry install
   ```

2. You might need to set your PYTHONPATH environment variable:

   ```sh
   export PYTHONPATH=$(pwd)
   ```

3. Then you're ready to go. You might need to set your PYTHONPATH environment variable:

   ```sh
   poetry run python ./examples/autobook.py
   ```

</details>

## Disclaimer

I'm not responsible for anything that goes wrong if you choose to use this. Enjoy responsibly.
