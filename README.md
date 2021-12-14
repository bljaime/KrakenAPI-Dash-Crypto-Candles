# Getting crypto trading data with Kraken API, VWAP calculation, interactive visualization using Dash and deployment with Heroku

Download trading data from a currency pair among several using [Kraken's REST API](https://docs.kraken.com/rest/) (specifically, [pykrakenapi](https://github.com/dominiktraxl/pykrakenapi) is used). Data processing with **Pandas**, calculation of **VWAP** indicator. Creation of an interactive application in **Dash**, combining different charts such as candlesticks, time series, bar charts, etc., and and styling with *.css*. Brief software testing. Deployment in the cloud with **Heroku**. Possibility of reproducing the virtual environment created using **Pipenv**.

## Files description

- */assets*
  - **favicon.ico**: Icon to display in the browser tab.
  - **style.css**: Style sheet.
- **.gitignore**: Indicates which files should be ignored by git.
- **app.py**: Dash application script.
- **currencies.py**: Script containing the Pair class.
- **Pipfile**: Ensures the creation of deterministic virtual environments with Pipenv.
- **Pipfile.lock**: Ensures the creation of deterministic virtual environments with Pipenv.
- **Procfile**: File used by gunicorn to launch the application.
- **requirements.txt**: Indicates the requirements for the correct handling of dependencies in Heroku.
- **runtime.txt**: Tells Heroku which version of Python to use.
- **test_pair.py**: Script corresponding to the testing part for the VWAP function.

## Heroku app site

This is what can be seen in the [Heroku site](https://ancient-coast-97559.herokuapp.com/): <p align="center"> <img src="/imgs/screenshot-heroku.PNG"/>
