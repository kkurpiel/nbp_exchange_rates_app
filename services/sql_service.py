from datetime import date
import pyodbc
from models.tables import Tables
from models.rates import Rates

class SqlService:
    ##### Konstruktor inicjalizujący połączenie z bazą danych #####
    def __init__(self, connection_string: str):
        self.conn = pyodbc.connect(connection_string)
    
    ##### Metoda wstawiająca wstawiająca rekord do tabeli NBP.Tables #####
    def insert_table(self, table: Tables) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""INSERT INTO [NBP].[Tables] ([table], [no], [effectiveDate], [tradingDate])
                          VALUES (?, ?, ?, ?)""", 
            (table.table, table.no, table.effectiveDate, table.tradingDate))
        self.conn.commit()

        cursor.execute("SELECT @@IDENTITY AS ident")
        row = cursor.fetchone()
        return int(row.ident)
    
    ##### Metoda wstawiająca rekord do tabeli NBP.Rates #####
    def insert_rate(self, tableId: int, rate: Rates):
        cursor = self.conn.cursor()
        cursor.execute("""INSERT INTO [NBP].[Rates] ([tableId], [currency], [code], [bid], [ask], [mid])
                            VALUES (?, ?, ?, ?, ?, ?)""", 
            (tableId, rate.currency, rate.code, rate.bid, rate.ask, rate.mid))
        self.conn.commit()

    ##### Metoda sprawdzająca istnienie rekordu w tabeli NBP.Tables #####
    def table_exists(self, table: Tables) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("""SELECT 1
                          FROM [NBP].[Tables] (NOLOCK)
                          WHERE 1 = 1
                          AND [table] = ? 
                          AND [no] = ?
                          AND [effectiveDate] = ?
                          AND (([tradingDate] = ?) OR ([tradingDate] IS NULL AND ? IS NULL))""",
                       (table.table, table.no, table.effectiveDate, table.tradingDate, table.tradingDate))
        row = cursor.fetchone()
        return row is not None
    
    ##### Metoda sprawdzająca istnienie rekordu w tabeli NBP.Rates #####
    def rate_exists(self, rate: Rates) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("""SELECT 1
                          FROM [NBP].[Rates] (NOLOCK)
                          WHERE 1 = 1
                          AND [currency] = ? 
                          AND [code] = ?
                          AND (([bid] = ?) OR ([bid] IS NULL AND ? IS NULL))
                          AND (([ask] = ?) OR ([ask] IS NULL AND ? IS NULL))
                          AND (([mid] = ?) OR ([mid] IS NULL AND ? IS NULL))""",
                       (rate.currency, rate.code, rate.bid, rate.bid, rate.ask, rate.ask, rate.mid, rate.mid))
        row = cursor.fetchone()
        return row is not None

    ##### Metoda pobierająca datę ostatniego rekordu dla danego typu tabeli #####
    def get_last_date(self, table_char: str) -> date:
        cursor = self.conn.cursor()
        cursor.execute("""SELECT MAX([effectiveDate]) AS lastDate
                          FROM [NBP].[Tables] (NOLOCK)
                          WHERE [table] = ?""",
                       (table_char))
        row = cursor.fetchone()
        if row and row.lastDate:
            return row.lastDate
        else:
            return date(2025, 10, 1)
    
    ##### Metoda pobierająca dane z bazy dla danego zakresu dat i typu tabeli #####
    def get_data(self, course_type: str, date_from: date, date_to: date, currencies: list) -> list:
        currency_list_params = ",".join("?" * len(currencies))
        params = [date_from, date_to] + currencies
        filter_clause = ""
        if course_type is not None and course_type != "":
            filter_clause = f"AND r.[{course_type}] IS NOT NULL"

        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT t.[table], 
                   t.[no], 
                   t.[effectiveDate],
                   t.[tradingDate],
                   r.[currency],
                   r.[code],
                   r.[mid],
                   r.[bid],
                   r.[ask]
            FROM [NBP].[Rates] r (NOLOCK)
            JOIN [NBP].[Tables] t (NOLOCK) ON r.[tableId] = t.[id]
            WHERE 1 = 1
            AND t.[effectiveDate] BETWEEN ? AND ?
            AND r.[code] IN ({currency_list_params})
            {filter_clause}
            ORDER BY r.[code], t.[effectiveDate]
        """, params)
        rows = [tuple(row) for row in cursor.fetchall()]
        cursor.close()
        return rows
    
    ##### Metoda pobierająca listę unikalnych walut z tabeli NBP.Rates #####
    def get_currencies(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT r.[code]
            FROM [NBP].[Rates] r (NOLOCK)
            ORDER BY r.[code]
        """)
        rows = [row.code for row in cursor.fetchall()]
        cursor.close()
        return rows