from config.init_settings import init_settings
import streamlit as st
from utils.logger import init_logger
from views.main_view import MainView

def main():
    logger = init_logger()
    logger.info("Rozpoczęcie działania aplikacji.")
    st.set_page_config(page_title="Kursy walut NBP", layout="wide")

    try:
        settings = init_settings()
    except Exception as ex:
        logger.exception(f"Błąd podczas inicjalizacji ustawień aplikacji: {ex}")

    menu_view = MainView(settings, logger)
    menu_view.render()
    logger.info("Zakończenie działania aplikacji.")

if __name__ == "__main__":
    main()
