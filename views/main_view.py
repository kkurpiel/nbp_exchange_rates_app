from logging import Logger
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

from services.api_service import ApiService
from services.sql_service import SqlService

class MainView:
    ##### Konstruktor widoku #####
    def __init__(self, settings: dict, logger: Logger):
        self.df = None
        self.settings = settings
        self.logger = logger
        self.sql_service = SqlService(settings["database"]["connection_string"])
        self.api_service = ApiService(settings["nbp_api"]["base_url"])

        try:
            self.update_data()
            self.currencies = self.sql_service.get_currencies()
        except Exception as ex:
            self.logger.exception(f"Błąd podczas inicjalizacji widoku menu: {ex}")
            st.error("Wystąpił błąd podczas inicjalizacji widoku menu.")

    ##### Metoda aktualizująca dane w bazie #####
    def update_data(self):
        try:
            for table_char in self.settings.get("tables", ["A", "B", "C"]):
                date_from = (self.sql_service.get_last_date(table_char) + timedelta(days=1)).date()
                date_to = date.today()
                if date_from > date_to:
                    continue
                tables = self.api_service.get_table_models(table_char, date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d"))
                if not tables:
                    continue
                self.logger.info(f"Pobrano {len(tables)} tabeli {table_char} z API (od {date_from} do {date_to}).")
                for table in tables:
                    if self.sql_service.table_exists(table):
                        continue
                    id = self.sql_service.insert_table(table)
                    for rate in table.rates:
                        if self.sql_service.rate_exists(rate):
                            continue
                        self.sql_service.insert_rate(id, rate)
        except Exception as ex:
            self.logger.exception(f"Błąd podczas pobierania danych: {ex}")
            st.error("Wystąpił błąd podczas pobierania danych.")

    ##### Metoda renderująca widok menu #####
    def render(self):
        try:
            st.title("Kursy walut NBP")

            col1, col2, col3 = st.columns(3)
            with col1:
                exchange_type = st.selectbox("Typ kursu:", options=self.settings["exchanges"], index=0)
            with col2:
                start_date = st.date_input("Data początkowa:", date.today() - timedelta(days=30))
            with col3:
                end_date = st.date_input("Data końcowa:", date.today())
            
            col4, col5, col6 = st.columns(3)
            with col4:
                selected_currencies = st.multiselect("Waluty:", options=self.currencies, default=[self.currencies[0]])
            with col5:
                plot_type_names = [p["name"] for p in self.settings["plot_types"]]
                plot_type = st.selectbox("Rodzaj wykresu:", options=plot_type_names, index=0)
            with col6:
                st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
                download_clicked = st.button("Pobierz dane")
        except Exception as ex:
            self.logger.exception(f"Błąd podczas renderowania widoku menu: {ex}")
            st.error("Wystąpił błąd podczas renderowania widoku menu.")
            return
        
        if download_clicked:
            try:
                if selected_currencies is None or len(selected_currencies) == 0:
                    st.warning("Wybierz walutę.")
                    return

                with st.spinner("Pobieranie danych z NBP..."):
                    rows = self.sql_service.get_data(exchange_type, start_date, end_date, selected_currencies)

                    plot_description = next(
                        (p["description"] for p in self.settings["plot_types"] if p["name"] == plot_type),
                        "Brak opisu dla tego wykresu."
                    )
                    st.info(f"**{plot_type}** — {plot_description}")
                    
                    if not rows:
                        st.warning("Brak danych w bazie dla wybranego zakresu.")
                        return
                    
                    self.df = pd.DataFrame(
                        rows,
                        columns=["table", "no", "effectiveDate", "tradingDate",
                                 "currency", "code", "mid", "bid", "ask"]
                    )
                    st.session_state["df"] = self.df
                    self.logger.info(f"Pobrano {len(self.df)} rekordów z bazy danych (od {start_date} do {end_date}).")
                    st.success(f"Pobrane rekordy z bazy danych: {len(self.df)}.")
            except Exception as ex:
                self.logger.exception(f"Błąd podczas pobierania danych z bazy danych: {ex}")
                st.error("Wystąpił błąd podczas pobierania danych z bazy danych.")
                return

            if self.df is not None and not self.df.empty:

                filtered = self.df[self.df["code"].isin(selected_currencies)]

                if filtered.empty:
                    self.logger.info("Brak danych dla wybranych walut.")
                    st.warning("Brak danych dla wybranych walut.")
                    return

                if plot_type == "Kurs w czasie":
                    try: 
                        fig = px.line(
                            filtered, 
                            x="effectiveDate", 
                            y=exchange_type, color="code", 
                            title=plot_type, 
                            labels={exchange_type: "Kurs", "effectiveDate": "Data"}
                        ) 
                    except Exception as ex: 
                        self.logger.exception(f"Błąd podczas tworzenia wykresu kursów: {ex}") 
                        st.error("Wystąpił błąd podczas tworzenia wykresu kursów.") 
                        return

                elif plot_type == "Zmiana dzienna (%)":
                    try:
                        filtered = (
                            filtered.sort_values(["code", "effectiveDate"])
                            .assign(change_pct=lambda x: x.groupby("code")[exchange_type].pct_change() * 100)
                        )
                        fig = px.bar(
                            filtered,
                            x="effectiveDate",
                            y="change_pct",
                            color="code",
                            title=plot_type,
                            labels={"change_pct": "Zmiana [%]", "effectiveDate": "Data"}
                        )
                    except Exception as ex:
                        self.logger.exception(f"Błąd podczas tworzenia wykresu zmiany dziennej: {ex}")
                        st.error("Wystąpił błąd podczas tworzenia wykresu zmiany dziennej.")
                        return

                elif plot_type == "Średnia krocząca (7 dni)":
                    try:
                        filtered = (
                            filtered.sort_values(["code", "effectiveDate"])
                            .assign(ma7=lambda x: x.groupby("code")[exchange_type].transform(lambda s: s.rolling(7).mean()))
                        )
                        fig = px.line(
                            filtered,
                            x="effectiveDate",
                            y="ma7",
                            color="code",
                            title=plot_type,
                            labels={"ma7": "Średnia 7-dniowa", "effectiveDate": "Data"}
                        )
                    except Exception as ex:
                        self.logger.exception(f"Błąd podczas tworzenia wykresu średniej kroczącej 7 dni: {ex}")
                        st.error("Wystąpił błąd podczas tworzenia wykresu średniej kroczącej 7 dni.")
                        return
                
                elif plot_type == "Odchylenie (7 dni)":
                    try:
                        filtered = (
                            filtered.sort_values(["code", "effectiveDate"])
                            .assign(
                                change=lambda x: x.groupby("code")[exchange_type].pct_change(),
                                volatility=lambda x: x.groupby("code")["change"].transform(lambda s: s.rolling(7).std() * 100)
                            )
                        )
                        fig = px.line(
                            filtered,
                            x="effectiveDate",
                            y="volatility",
                            color="code",
                            title=plot_type,
                            labels={"volatility": "Odchylenie [%]", "effectiveDate": "Data"}
                        )
                    except Exception as ex:
                        self.logger.exception(f"Błąd podczas tworzenia wykresu odchylenia (7 dni): {ex}")
                        st.error("Wystąpił błąd podczas tworzenia wykresu odchylenia (7 dni).")
                        return
                    
                elif plot_type == "Relacja walut":
                    try:
                        if len(selected_currencies) != 2:
                            st.warning("Aby zobaczyć relację walut, wybierz dokładnie 2 waluty.")
                            return
                        
                        c1, c2 = selected_currencies
                        df_pivot = (
                            filtered.pivot(index="effectiveDate", columns="code", values=exchange_type)
                            .dropna()
                        )
                        df_pivot["ratio"] = df_pivot[c1] / df_pivot[c2]

                        fig = px.line(
                            df_pivot,
                            x=df_pivot.index,
                            y="ratio",
                            title=f"{plot_type} {c1}/{c2}",
                            labels={"ratio": f"Stosunek {c1}/{c2}", "effectiveDate": "Data"}
                        )
                    except Exception as ex:
                        self.logger.exception(f"Błąd podczas tworzenia wykresu relacji walut: {ex}")
                        st.error("Wystąpił błąd podczas tworzenia wykresu relacji walut.")
                        return
                
                elif plot_type == "Wskaźnik siły waluty":
                    try:
                        filtered = (
                            filtered.sort_values(["code", "effectiveDate"])
                            .assign(
                                strength=lambda x: x.groupby("code")[exchange_type].transform(
                                    lambda s: s / s.iloc[0] * 100
                                )
                            )
                        )
                        fig = px.line(
                            filtered,
                            x="effectiveDate",
                            y="strength",
                            color="code",
                            title=plot_type,
                            labels={"strength": "Indeks (100=Start)", "effectiveDate": "Data"}
                        )
                    except Exception as ex:
                        self.logger.exception(f"Błąd podczas tworzenia wskaźnika siły waluty: {ex}")
                        st.error("Wystąpił błąd podczas tworzenia wskaźnika siły waluty.")
                        return
                    
                elif plot_type == "Korelacja pomiędzy kursami walut":
                    try:
                        corr = filtered.pivot(index="effectiveDate", columns="code", values=exchange_type).corr()
                        fig = px.imshow(corr, text_auto=True, title=plot_type)
                    except Exception as ex:
                        self.logger.exception(f"Błąd podczas tworzenia mapy korelacji: {ex}")
                        st.error("Wystąpił błąd podczas tworzenia mapy korelacji.")
                        return

                else:
                    self.logger.exception(f"W aplikacji nie zaimplementowano wykresu: {plot_type}.")
                    st.error(f"W aplikacji nie zaimplementowano wykresu: {plot_type}.")
                    return

                st.plotly_chart(fig, width='stretch')
                if self.settings.get("show_dataframe", True):
                    st.dataframe(filtered)
