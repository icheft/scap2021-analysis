# SCAP Data Analysis

## Telegram Analysis

With some help from expectocode's [telegram-analysis](https://github.com/expectocode/telegram-analysis#examples).


## Color Code

![Image](https://i.imgur.com/DL9yiaN.png)

| Item    | Hex      |
| ------- | -------- |
| YouTube | `ff6000` |
| HaHow   | `ff9100` |
| Comm    | `f4af00` |
| others  | `c9c9c9` |
| all     | `FECF0F` |

## Streamlit 

1. Configuration:
    + you should create a new file named `.streamlit/secrets.toml`
    + set `public_gsheets_url = "URL"` (now using `public_data` in our shared folder under `Projects/問卷資料/data`)
    + set the constant variable `DEPLOY_TO_HEROKU = False` in `app.py`
2. Run:
    ```sh
    pip install -r requirements.txt
    streamlit run app.py
    ```
